using UnrealBuildTool;
public class EternalRebirth : ModuleRules {
    public EternalRebirth(ReadOnlyTargetRules Target) : base(Target) {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] {"Core", "CoreUObject", "Engine", "InputCore", "RenderCore"});
    }
}
