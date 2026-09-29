#include "Modules/ModuleManager.h"
// Epic's installed Windows binaries are built with MSVC and do not export the
// Clang-only Windows namespace wrapper. Its x64 ABI equals the kernel32 import.
#if defined(__clang__) && PLATFORM_WINDOWS && PLATFORM_64BITS
#pragma comment(lib, "kernel32.lib")
#pragma comment(linker, "/alternatename:__imp_?GetCurrentThreadId@Windows@@YAKXZ=__imp_GetCurrentThreadId")
#endif
IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, EternalRebirth, "EternalRebirth");
