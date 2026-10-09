/* Private-job lifecycle launcher; filesystem/network policy belongs to Python. */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <tlhelp32.h>
#include <aclapi.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#ifndef _M_X64
#error This launcher supports native Windows x64 only.
#endif

#define COMMAND_UNITS 32768
#define CONFIG_HEADER 20
#define CONFIG_MAX (CONFIG_HEADER + 4 * COMMAND_UNITS)

typedef struct {
    DWORD flags;
    wchar_t *interpreter;
    wchar_t *source;
    HANDLE executable;
    HANDLE stream;
} CONFIG;

static void report_error(const char *operation, DWORD error) {
    fprintf(stderr, "private-job launcher: %s failed (Windows error %lu)\n",
            operation, (unsigned long)error);
}

static uint32_t read_u32(const unsigned char *value) {
    return (uint32_t)value[0] | ((uint32_t)value[1] << 8) |
           ((uint32_t)value[2] << 16) | ((uint32_t)value[3] << 24);
}

static wchar_t *read_string(const unsigned char *bytes, uint32_t units) {
    wchar_t *text = calloc((size_t)units + 1, sizeof(wchar_t));
    uint32_t index;
    if (!text) {
        SetLastError(ERROR_NOT_ENOUGH_MEMORY);
        return NULL;
    }
    for (index = 0; index < units; ++index) {
        unsigned value = bytes[2 * index] | ((unsigned)bytes[2 * index + 1] << 8);
        if (!value) {
            free(text);
            SetLastError(ERROR_INVALID_DATA);
            return NULL;
        }
        text[index] = (wchar_t)value;
    }
    for (index = 0; index < units; ++index) {
        unsigned value = text[index];
        if (value >= 0xD800 && value <= 0xDBFF) {
            if (++index >= units || text[index] < 0xDC00 || text[index] > 0xDFFF) {
                free(text);
                SetLastError(ERROR_INVALID_DATA);
                return NULL;
            }
        } else if (value >= 0xDC00 && value <= 0xDFFF) {
            free(text);
            SetLastError(ERROR_INVALID_DATA);
            return NULL;
        }
    }
    return text;
}

static BOOL check_file_security(HANDLE file) {
    HANDLE token = NULL;
    DWORD token_size = 0, error = ERROR_INVALID_SECURITY_DESCR, index;
    TOKEN_USER *user = NULL;
    PSECURITY_DESCRIPTOR descriptor = NULL;
    PSID owner = NULL;
    PACL dacl = NULL;
    SECURITY_DESCRIPTOR_CONTROL control;
    DWORD revision;
    BYTE system_buffer[SECURITY_MAX_SID_SIZE];
    PSID system = system_buffer;
    DWORD system_size = sizeof(system_buffer);
    BOOL ok = FALSE, user_allowed = FALSE;
    error = GetSecurityInfo(file, SE_FILE_OBJECT,
                            OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,
                            &owner, NULL, &dacl, NULL, &descriptor);
    if (error != ERROR_SUCCESS) goto done;
    error = ERROR_INVALID_SECURITY_DESCR;
    if (!dacl || !GetSecurityDescriptorControl(descriptor, &control, &revision) ||
        !(control & SE_DACL_PROTECTED)) goto done;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) {
        error = GetLastError();
        goto done;
    }
    GetTokenInformation(token, TokenUser, NULL, 0, &token_size);
    if (!token_size) {
        error = GetLastError();
        goto done;
    }
    user = malloc(token_size);
    if (!user) {
        error = ERROR_NOT_ENOUGH_MEMORY;
        goto done;
    }
    if (!GetTokenInformation(token, TokenUser, user, token_size, &token_size) ||
        !CreateWellKnownSid(WinLocalSystemSid, NULL, system, &system_size)) {
        error = GetLastError();
        goto done;
    }
    if (!owner || !EqualSid(owner, user->User.Sid)) goto done;
    for (index = 0; index < dacl->AceCount; ++index) {
        ACCESS_ALLOWED_ACE *ace;
        PSID sid;
        if (!GetAce(dacl, index, (void **)&ace)) goto done;
        if (ace->Header.AceType != ACCESS_ALLOWED_ACE_TYPE ||
            ace->Header.AceFlags != 0) goto done;
        sid = (PSID)&ace->SidStart;
        if (!IsValidSid(sid) ||
            (!EqualSid(sid, user->User.Sid) && !EqualSid(sid, system))) goto done;
        if (EqualSid(sid, user->User.Sid) &&
            (ace->Mask & (FILE_READ_DATA | READ_CONTROL)) ==
                (FILE_READ_DATA | READ_CONTROL)) user_allowed = TRUE;
    }
    if (!user_allowed) goto done;
    ok = TRUE;
done:
    if (descriptor) LocalFree(descriptor);
    if (token) CloseHandle(token);
    free(user);
    if (!ok) SetLastError(error);
    return ok;
}

static BOOL read_config(CONFIG *config) {
    wchar_t path[COMMAND_UNITS];
    DWORD length = GetModuleFileNameW(NULL, path, COMMAND_UNITS);
    HANDLE file = INVALID_HANDLE_VALUE;
    FILE_ATTRIBUTE_TAG_INFO attributes;
    FILE_ID_INFO executable_id, stream_id;
    LARGE_INTEGER size;
    unsigned char *bytes = NULL;
    DWORD read = 0, error = ERROR_INVALID_DATA;
    uint32_t interpreter_units, source_units;
    BOOL ok = FALSE;
    if (!length || length >= COMMAND_UNITS) {
        SetLastError(ERROR_FILENAME_EXCED_RANGE);
        return FALSE;
    }
    config->executable = CreateFileW(
        path, GENERIC_READ | READ_CONTROL, FILE_SHARE_READ, NULL, OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    if (config->executable == INVALID_HANDLE_VALUE) {
        config->executable = NULL;
        return FALSE;
    }
    if (!GetFileInformationByHandleEx(config->executable, FileAttributeTagInfo,
                                      &attributes, sizeof(attributes)) ||
        !GetFileInformationByHandleEx(config->executable, FileIdInfo,
                                      &executable_id, sizeof(executable_id)))
        return FALSE;
    if ((attributes.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) ||
        GetFileType(config->executable) != FILE_TYPE_DISK) {
        SetLastError(ERROR_INVALID_DATA);
        return FALSE;
    }
    if (!check_file_security(config->executable)) return FALSE;
    length = GetFinalPathNameByHandleW(config->executable, path, COMMAND_UNITS,
                                       FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
    if (!length || length + 17 >= COMMAND_UNITS) {
        SetLastError(ERROR_FILENAME_EXCED_RANGE);
        return FALSE;
    }
    wcscat_s(path, COMMAND_UNITS, L":omnigent.config");
    file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
                       FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    if (file == INVALID_HANDLE_VALUE) return FALSE;
    config->stream = file;
    if (!GetFileInformationByHandleEx(file, FileIdInfo, &stream_id,
                                      sizeof(stream_id))) {
        error = GetLastError();
        goto done;
    }
    if (memcmp(&executable_id, &stream_id, sizeof(executable_id))) goto done;
    if (!GetFileSizeEx(file, &size)) {
        error = GetLastError();
        goto done;
    }
    if (size.QuadPart < CONFIG_HEADER || size.QuadPart > CONFIG_MAX) goto done;
    bytes = malloc((size_t)size.QuadPart);
    if (!bytes) {
        error = ERROR_NOT_ENOUGH_MEMORY;
        goto done;
    }
    if (!ReadFile(file, bytes, (DWORD)size.QuadPart, &read, NULL)) {
        error = GetLastError();
        goto done;
    }
    if (read != size.QuadPart || memcmp(bytes, "OJLCFG01", 8)) goto done;
    config->flags = read_u32(bytes + 8);
    interpreter_units = read_u32(bytes + 12);
    source_units = read_u32(bytes + 16);
    if (config->flags & ~1u || !interpreter_units || !source_units ||
        interpreter_units >= COMMAND_UNITS || source_units >= COMMAND_UNITS ||
        CONFIG_HEADER + 2ULL * (interpreter_units + source_units) !=
            (unsigned long long)size.QuadPart) goto done;
    config->interpreter = read_string(bytes + CONFIG_HEADER, interpreter_units);
    if (!config->interpreter) {
        error = GetLastError();
        goto done;
    }
    config->source = read_string(bytes + CONFIG_HEADER + 2 * interpreter_units,
                                 source_units);
    if (!config->source) {
        error = GetLastError();
        goto done;
    }
    /* Only drive-rooted and UNC paths may select the interpreter. */
    if (!((interpreter_units >= 3 &&
           ((config->interpreter[0] >= L'A' && config->interpreter[0] <= L'Z') ||
            (config->interpreter[0] >= L'a' && config->interpreter[0] <= L'z')) &&
           config->interpreter[1] == L':' &&
           (config->interpreter[2] == L'\\' || config->interpreter[2] == L'/')) ||
          (interpreter_units >= 3 && config->interpreter[0] == L'\\' &&
           config->interpreter[1] == L'\\'))) goto done;
    ok = TRUE;
done:
    free(bytes);
    if (!ok) SetLastError(error);
    return ok;
}

static BOOL parent_is_alive(HANDLE parent) {
    DWORD result = WaitForSingleObject(parent, 0);
    if (result == WAIT_TIMEOUT) return TRUE;
    if (result != WAIT_FAILED) SetLastError(ERROR_PROCESS_ABORTED);
    return FALSE;
}

static HANDLE capture_parent(void) {
    HANDLE snapshot, parent = NULL;
    PROCESSENTRY32W entry = {0};
    DWORD parent_pid = 0, error = ERROR_NOT_FOUND;
    FILETIME own_created, parent_created, exited, kernel, user;
    if (!GetProcessTimes(GetCurrentProcess(), &own_created, &exited, &kernel, &user))
        return NULL;
    snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return NULL;
    entry.dwSize = sizeof(entry);
    if (Process32FirstW(snapshot, &entry)) {
        do {
            if (entry.th32ProcessID == GetCurrentProcessId()) {
                parent_pid = entry.th32ParentProcessID;
                break;
            }
        } while (Process32NextW(snapshot, &entry));
    }
    CloseHandle(snapshot);
    if (!parent_pid || parent_pid == GetCurrentProcessId()) {
        SetLastError(error);
        return NULL;
    }
    parent = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION,
                          FALSE, parent_pid);
    if (!parent) return NULL;
    if (!GetProcessTimes(parent, &parent_created, &exited, &kernel, &user))
        goto fail;
    if (CompareFileTime(&parent_created, &own_created) > 0) {
        SetLastError(ERROR_INVALID_DATA);
        goto fail;
    }
    if (!parent_is_alive(parent)) goto fail;
    return parent;
fail:
    error = GetLastError();
    CloseHandle(parent);
    SetLastError(error);
    return NULL;
}

static BOOL append_char(wchar_t *command, size_t *used, wchar_t value) {
    if (*used >= COMMAND_UNITS - 1) {
        SetLastError(ERROR_BUFFER_OVERFLOW);
        return FALSE;
    }
    command[(*used)++] = value;
    command[*used] = L'\0';
    return TRUE;
}

static BOOL append_repeat(wchar_t *command, size_t *used, wchar_t value,
                          size_t count) {
    while (count--) {
        if (!append_char(command, used, value)) return FALSE;
    }
    return TRUE;
}

static BOOL append_argument(wchar_t *command, size_t *used, const wchar_t *arg) {
    size_t slashes;
    if (*used && !append_char(command, used, L' ')) return FALSE;
    if (!append_char(command, used, L'"')) return FALSE;
    for (;;) {
        slashes = 0;
        while (*arg == L'\\') {
            ++slashes;
            ++arg;
        }
        if (*arg == L'"' || !*arg) {
            if (!append_repeat(command, used, L'\\', 2 * slashes)) return FALSE;
            if (!*arg) break;
            if (!append_char(command, used, L'\\')) return FALSE;
        } else if (!append_repeat(command, used, L'\\', slashes)) return FALSE;
        if (!append_char(command, used, *arg++)) return FALSE;
    }
    return append_char(command, used, L'"');
}

static HANDLE duplicate_stdio(DWORD standard, BOOL input) {
    HANDLE original = GetStdHandle(standard), duplicate = NULL;
    DWORD ignored;
    if (original && original != INVALID_HANDLE_VALUE &&
        GetHandleInformation(original, &ignored)) {
        if (!DuplicateHandle(GetCurrentProcess(), original, GetCurrentProcess(),
                             &duplicate, 0, TRUE, DUPLICATE_SAME_ACCESS)) return NULL;
        return duplicate;
    }
    /* A detached/no-console caller may have no standard handle. */
    {
        SECURITY_ATTRIBUTES security = {sizeof(security), NULL, TRUE};
        duplicate = CreateFileW(L"NUL", input ? GENERIC_READ : GENERIC_WRITE,
                                FILE_SHARE_READ | FILE_SHARE_WRITE, &security,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        return duplicate == INVALID_HANDLE_VALUE ? NULL : duplicate;
    }
}

#ifdef OMNIGENT_TEST_CHECKPOINTS
static BOOL test_checkpoint(const wchar_t *stage) {
    wchar_t selected[64], ready_name[256], release_name[256];
    HANDLE ready = NULL, release = NULL;
    DWORD length, error = ERROR_INVALID_DATA;
    BOOL ok = FALSE;
    length = GetEnvironmentVariableW(L"OMNIGENT_LAUNCHER_TEST_CHECKPOINT",
                                     selected, 64);
    if (!length) return TRUE;
    if (length >= 64) {
        SetLastError(ERROR_INVALID_DATA);
        return FALSE;
    }
    if (wcscmp(selected, stage)) return TRUE;
    length = GetEnvironmentVariableW(L"OMNIGENT_LAUNCHER_TEST_READY_EVENT",
                                     ready_name, 256);
    if (!length || length >= 256) goto done;
    length = GetEnvironmentVariableW(L"OMNIGENT_LAUNCHER_TEST_RELEASE_EVENT",
                                     release_name, 256);
    if (!length || length >= 256) goto done;
    ready = OpenEventW(EVENT_MODIFY_STATE, FALSE, ready_name);
    if (!ready) {
        error = GetLastError();
        goto done;
    }
    release = OpenEventW(SYNCHRONIZE, FALSE, release_name);
    if (!release || !SetEvent(ready)) {
        error = GetLastError();
        goto done;
    }
    if (WaitForSingleObject(release, 60000) != WAIT_OBJECT_0) {
        error = ERROR_TIMEOUT;
        goto done;
    }
    ok = TRUE;
done:
    if (release) CloseHandle(release);
    if (ready) CloseHandle(ready);
    if (!ok) SetLastError(error);
    return ok;
}

static BOOL test_flag(const wchar_t *name) {
    wchar_t flag[2];
    return GetEnvironmentVariableW(name, flag, 2) == 1 && flag[0] == L'1';
}
#else
#define test_checkpoint(stage) TRUE
#endif

int wmain(int argc, wchar_t **argv) {
    CONFIG config = {0};
    STARTUPINFOEXW startup = {0};
    PROCESS_INFORMATION process = {0};
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = {0};
    HANDLE job = NULL, parent = NULL, stdio[3] = {NULL, NULL, NULL};
    wchar_t *command = NULL;
    SIZE_T attributes_size = 0;
    size_t used = 0;
    DWORD exit_code = 125, error;
    DWORD creation_flags = EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED;
    BOOL attributes_initialized = FALSE, success = FALSE;
    const char *operation = "read executable configuration stream";
    int index;
    if (!read_config(&config)) goto fail;
    if (config.flags & 1) {
        operation = "before-parent-capture test checkpoint";
        if (!test_checkpoint(L"before_parent_capture")) goto fail;
        operation = "capture live immediate parent";
        parent = capture_parent();
        if (!parent) goto fail;
    }
    command = calloc(COMMAND_UNITS, sizeof(wchar_t));
    operation = "allocate command line";
    if (!command) {
        SetLastError(ERROR_NOT_ENOUGH_MEMORY);
        goto fail;
    }
    operation = "encode command line";
    if (!append_argument(command, &used, config.interpreter) ||
        !append_argument(command, &used, L"-c") ||
        !append_argument(command, &used, config.source)) goto fail;
    for (index = 1; index < argc; ++index) {
        if (!append_argument(command, &used, argv[index])) goto fail;
    }
    if (config.flags & 1) {
        operation = "create private job";
#ifdef OMNIGENT_TEST_CHECKPOINTS
        if (test_flag(L"OMNIGENT_LAUNCHER_TEST_FAIL_JOB")) {
            SetLastError(ERROR_ACCESS_DENIED);
            goto fail;
        }
#endif
        job = CreateJobObjectW(NULL, NULL);
        if (!job) goto fail;
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        operation = "configure private job";
        if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                     &limits, sizeof(limits))) goto fail;
    }
    operation = "duplicate standard handles";
    stdio[0] = duplicate_stdio(STD_INPUT_HANDLE, TRUE);
    stdio[1] = duplicate_stdio(STD_OUTPUT_HANDLE, FALSE);
    stdio[2] = duplicate_stdio(STD_ERROR_HANDLE, FALSE);
    if (!stdio[0] || !stdio[1] || !stdio[2]) goto fail;
    operation = "allocate process attributes";
    InitializeProcThreadAttributeList(NULL, job ? 2 : 1, 0, &attributes_size);
    if (!attributes_size) goto fail;
    startup.lpAttributeList = HeapAlloc(GetProcessHeap(), 0, attributes_size);
    if (!startup.lpAttributeList) {
        SetLastError(ERROR_NOT_ENOUGH_MEMORY);
        goto fail;
    }
    if (!InitializeProcThreadAttributeList(startup.lpAttributeList, job ? 2 : 1,
                                           0, &attributes_size)) goto fail;
    attributes_initialized = TRUE;
    operation = "limit inherited handles";
    if (!UpdateProcThreadAttribute(startup.lpAttributeList, 0,
                                   PROC_THREAD_ATTRIBUTE_HANDLE_LIST, stdio,
                                   sizeof(stdio), NULL, NULL)) goto fail;
    operation = "assign private job at creation";
    if (job && !UpdateProcThreadAttribute(startup.lpAttributeList, 0,
                                          PROC_THREAD_ATTRIBUTE_JOB_LIST, &job,
                                          sizeof(job), NULL, NULL)) goto fail;
    startup.StartupInfo.cb = sizeof(startup);
    startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput = stdio[0];
    startup.StartupInfo.hStdOutput = stdio[1];
    startup.StartupInfo.hStdError = stdio[2];
    operation = "before-create test checkpoint";
    if (!test_checkpoint(L"before_create")) goto fail;
    operation = "check immediate parent before creation";
    if (parent && !parent_is_alive(parent)) goto fail;
    operation = "create child with process attributes";
    if (!CreateProcessW(config.interpreter, command, NULL, NULL, TRUE,
                         creation_flags, NULL, NULL, &startup.StartupInfo,
                         &process)) goto fail;
    operation = "after-create test checkpoint";
    if (!test_checkpoint(L"after_create")) goto fail;
    operation = "check immediate parent before resume";
    if (parent && !parent_is_alive(parent)) goto fail;
    operation = "resume child";
#ifdef OMNIGENT_TEST_CHECKPOINTS
    if (test_flag(L"OMNIGENT_LAUNCHER_TEST_FAIL_RESUME")) {
        SetLastError(ERROR_ACCESS_DENIED);
        goto fail;
    }
#endif
    if (ResumeThread(process.hThread) == (DWORD)-1) goto fail;
    CloseHandle(process.hThread);
    process.hThread = NULL;
    operation = "after-resume test checkpoint";
    if (!test_checkpoint(L"after_resume")) goto fail;
    operation = "wait for child or immediate parent";
    if (parent) {
        HANDLE waits[2] = {parent, process.hProcess};
        DWORD result = WaitForMultipleObjects(2, waits, FALSE, INFINITE);
        if (result != WAIT_OBJECT_0 + 1) {
            if (result != WAIT_FAILED) SetLastError(ERROR_PROCESS_ABORTED);
            goto fail;
        }
    } else if (WaitForSingleObject(process.hProcess, INFINITE) != WAIT_OBJECT_0)
        goto fail;
    operation = "read child exit code";
    if (!GetExitCodeProcess(process.hProcess, &exit_code)) goto fail;
    success = TRUE;
    goto done;
fail:
    error = GetLastError();
    report_error(operation, error);
done:
    /* Close first so parent death kills the complete tree immediately. */
    if (job) CloseHandle(job);
    if (!success && process.hProcess) {
        TerminateProcess(process.hProcess, 125);
        WaitForSingleObject(process.hProcess, 5000);
    }
    if (parent) CloseHandle(parent);
    if (process.hThread) CloseHandle(process.hThread);
    if (process.hProcess) CloseHandle(process.hProcess);
    if (attributes_initialized) DeleteProcThreadAttributeList(startup.lpAttributeList);
    if (startup.lpAttributeList) HeapFree(GetProcessHeap(), 0, startup.lpAttributeList);
    for (index = 0; index < 3; ++index) {
        if (stdio[index]) CloseHandle(stdio[index]);
    }
    free(command);
    free(config.interpreter);
    free(config.source);
    if (config.stream) CloseHandle(config.stream);
    if (config.executable) CloseHandle(config.executable);
    return (int)exit_code;
}
