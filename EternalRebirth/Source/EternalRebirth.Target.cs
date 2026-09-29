using UnrealBuildTool;
public class EternalRebirthTarget : TargetRules {
    public EternalRebirthTarget(TargetInfo Target) : base(Target) {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.Add("EternalRebirth");
        WindowsPlatform.Compiler = WindowsCompiler.Clang;
        WindowsPlatform.CompilerVersion = "20.1.8";
        WindowsPlatform.ToolchainVersion = "14.38.33130";
        WindowsPlatform.bAllowClangLinker = false;
    }
}
