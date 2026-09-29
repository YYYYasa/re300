#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CombatAssetTools.generated.h"
class UBlendSpace1D;
class UStaticMesh;
UCLASS()
class ETERNALREBIRTH_API UCombatAssetTools : public UBlueprintFunctionLibrary {
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Combat Import")
    static void FinalizeMovementAssets(UBlendSpace1D* Blend, UStaticMesh* Floor);
};
