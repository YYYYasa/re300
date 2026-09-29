#include "CombatAssetTools.h"
#include "Animation/BlendSpace1D.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/BodySetup.h"

void UCombatAssetTools::FinalizeMovementAssets(UBlendSpace1D* Blend,UStaticMesh* Floor) {
#if WITH_EDITOR
    if(Blend) {
        Blend->ValidateSampleData();
        Blend->ResampleData();
        Blend->MarkPackageDirty();
        TArray<FBlendSampleData> Samples;
        int32 Index=INDEX_NONE;
        const bool Valid=Blend->GetSamplesFromBlendInput(FVector(.5,0,0),Samples,Index,true);
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_ASSET_BLEND valid=%d samples=%d"),Valid,Samples.Num());
    }
    if(Floor && Floor->GetBodySetup()) {
        auto Body=Floor->GetBodySetup();
        Body->CollisionTraceFlag=CTF_UseComplexAsSimple;
        Body->bDoubleSidedGeometry=true;
        Floor->Build(false);
        Body->InvalidatePhysicsData();
        Body->CreatePhysicsMeshes();
        Floor->MarkPackageDirty();
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_ASSET_FLOOR triangles=%d"),Body->TriMeshGeometries.Num());
    }
#endif
}
