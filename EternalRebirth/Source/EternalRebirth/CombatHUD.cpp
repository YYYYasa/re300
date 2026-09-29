#include "CombatPrototype.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Kismet/GameplayStatics.h"

void ACombatArenaHUD::BeginPlay() {
    Super::BeginPlay();
    Portrait=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Art/Heroes/H100/UI/T_H100_Portrait.T_H100_Portrait"));
    SealIcon=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Art/Heroes/H100/Effects/Textures/T_tx_tuxing_0037.T_tx_tuxing_0037"));
    CharmIcon=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Art/Heroes/H100/Effects/Textures/T_tx_tuxing_1254.T_tx_tuxing_1254"));
}

void ACombatArenaHUD::DrawPolishedHUD() {
    if(!Canvas) return;
    auto Hero=Cast<ACombatHeroPawn>(UGameplayStatics::GetPlayerPawn(this,0));
    if(!Hero) return;
    const float W=Canvas->SizeX,H=Canvas->SizeY,S=FMath::Min(W/1600.f,H/900.f);
    const FLinearColor Ivory(.94f,.92f,.84f,1),Gold(.76f,.63f,.39f,1),Muted(.63f,.70f,.74f,1);
    const FLinearColor Navy(.018f,.027f,.045f,.82f),Green(.42f,.83f,.58f,1);
    auto Text=[&](const FString& T,float X,float Y,float Size,FLinearColor C) {
        DrawText(T,FLinearColor(0,0,0,.72f),X+S,Y+S,GEngine->GetMediumFont(),Size*S*1.45f);
        DrawText(T,C,X,Y,GEngine->GetMediumFont(),Size*S*1.45f);
    };
    auto Ring=[&](float X,float Y,float R,FLinearColor C,float Fraction=1.f,float Thickness=1.f) {
        const int32 Segments=FMath::Max(1,FMath::CeilToInt(80*Fraction));
        for(int32 I=0;I<Segments;++I) {
            const float A=-PI/2+2*PI*Fraction*I/Segments,B=-PI/2+2*PI*Fraction*(I+1)/Segments;
            DrawLine(X+FMath::Cos(A)*R,Y+FMath::Sin(A)*R,X+FMath::Cos(B)*R,Y+FMath::Sin(B)*R,C,Thickness*S);
        }
    };
    auto Disk=[&](float X,float Y,float R,FLinearColor C) {
        Canvas->K2_DrawPolygon(nullptr,FVector2D(X,Y),FVector2D(R,R),64,C);
    };
    auto Icon=[&](UTexture2D* T,float X,float Y,float Size,float Alpha=1.f) {
        if(T) Canvas->K2_DrawTexture(T,FVector2D(X,Y),FVector2D(Size,Size),FVector2D::ZeroVector,
            FVector2D(1,1),FLinearColor(1,1,1,Alpha),BLEND_Translucent);
    };
    auto Diamond=[&](float X,float Y,float R,FLinearColor C) {
        DrawLine(X,Y-R,X+R,Y,C,S); DrawLine(X+R,Y,X,Y+R,C,S);
        DrawLine(X,Y+R,X-R,Y,C,S); DrawLine(X-R,Y,X,Y-R,C,S);
    };

    // Compass and field identity leave the center of the arena unobstructed.
    Disk(78*S,78*S,46*S,Navy); Ring(78*S,78*S,46*S,Gold); Ring(78*S,78*S,39*S,Muted);
    Text(TEXT("N"),73*S,25*S,.68f,Ivory);
    Diamond(78*S,78*S,15*S,Ivory);
    Text(TEXT("ETERNAL ARENA"),144*S,49*S,1.05f,Ivory);
    Text(TEXT("FIELD PRACTICE  /  H100"),145*S,79*S,.60f,Muted);
    DrawLine(145*S,108*S,325*S,108*S,Gold,S);

    const float Right=W-292*S;
    DrawRect(Navy,Right,35*S,260*S,66*S);
    DrawRect(Gold,Right,35*S,2*S,66*S);
    Text(Hero->IsAnimeStyle()?TEXT("ANIME"):TEXT("REALISTIC"),Right+18*S,44*S,.8f,Ivory);
    Text(TEXT("TAB"),W-76*S,45*S,.64f,Gold);
    Text(FString::Printf(TEXT("CAMERA  %.1f m   /   WHEEL"),Hero->ZoomDistance()/100.f),Right+18*S,76*S,.56f,Muted);

    if(auto Target=Hero->GetTarget()) {
        const float X=W/2-210*S,Y=41*S,Bar=420*S;
        Text(TEXT("TRAINING TARGET"),W/2-85*S,18*S,.65f,Ivory);
        DrawRect(Navy,X-10*S,Y-3*S,Bar+20*S,29*S);
        DisplayedTargetHealth=FMath::FInterpTo(DisplayedTargetHealth,Target->Health,GetWorld()->GetDeltaSeconds(),2.5f);
        DrawRect(FLinearColor(.17f,.18f,.21f,1),X,Y,Bar,6*S);
        DrawRect(Gold,X,Y,Bar*FMath::Clamp(DisplayedTargetHealth/Target->MaxHealth,0.f,1.f),6*S);
        DrawRect(FLinearColor(.82f,.29f,.29f,1),X,Y,Bar*Target->Health/Target->MaxHealth,6*S);
        Diamond(X-10*S,Y+3*S,4*S,Gold); Diamond(X+Bar+10*S,Y+3*S,4*S,Gold);
        Text(FString::Printf(TEXT("H013   /   %.0f : %.0f"),Target->Health,Target->MaxHealth),W/2-68*S,Y+11*S,.52f,Muted);
        const float Age=GetWorld()->GetTimeSeconds()-Target->LastHitTime;
        FVector2D P;
        if(Age>=0 && Age<.85f && GetOwningPlayerController()->ProjectWorldLocationToScreen(Target->GetActorLocation()+FVector(0,0,125),P)) {
            Text(FString::Printf(TEXT("%.0f"),Target->LastDamage),P.X-12*S,P.Y-Age*65*S,1.8f,FLinearColor(1,.84f,.48f,1-Age/.85f));
        }
    }

    const float Bottom=H-114*S;
    DrawRect(Navy,34*S,Bottom-8*S,306*S,94*S);
    Icon(Portrait,40*S,Bottom-3*S,82*S);
    DrawLine(40*S,Bottom-5*S,122*S,Bottom-5*S,Gold,2);
    DrawLine(40*S,Bottom+80*S,122*S,Bottom+80*S,Gold,2);
    Text(TEXT("HAKUREI REIMU"),138*S,Bottom+12*S,.94f,Ivory);
    Text(TEXT("SPIRIT SIGN  /  H100"),138*S,Bottom+43*S,.57f,Muted);
    Diamond(318*S,Bottom+67*S,5*S,Gold);

    const float HPX=W/2-170*S,HPY=H-62*S;
    Text(TEXT("HP"),HPX,HPY-21*S,.58f,Ivory);
    Text(FString::Printf(TEXT("%.0f / %.0f"),Hero->Health,Hero->MaxHealth),W/2-40*S,HPY-21*S,.58f,Ivory);
    DrawRect(Navy,HPX-4*S,HPY-4*S,348*S,14*S);
    DrawRect(Green,HPX,HPY,340*S*Hero->Health/Hero->MaxHealth,5*S);
    Diamond(HPX-8*S,HPY+2*S,4*S,Gold); Diamond(HPX+348*S,HPY+2*S,4*S,Gold);
    Text(TEXT("RMB  MOVE      WASD  WALK      R  RESET"),W/2-146*S,H-31*S,.52f,Muted);

    auto Ability=[&](float X,float Y,float R,UTexture2D* Texture,const TCHAR* Key,const TCHAR* Label,float Cooldown,float Total) {
        Disk(X,Y,R,Navy); Ring(X,Y,R+4*S,FLinearColor(.46f,.46f,.42f,.6f));
        Icon(Texture,X-R*.65f,Y-R*.65f,R*1.3f,Cooldown>0?.28f:.96f);
        Ring(X,Y,R,Gold,Cooldown>0?1-Cooldown/Total:1,2.f);
        if(Cooldown>0) Text(FString::Printf(TEXT("%.1f"),Cooldown),X-15*S,Y-12*S,1.35f,Ivory);
        DrawRect(FLinearColor(.9f,.88f,.80f,1),X-20*S,Y+R-7*S,40*S,19*S);
        Text(Key,X-12*S,Y+R-6*S,.58f,FLinearColor(.07f,.09f,.12f,1));
        Text(Label,X-R,Y+R+22*S,.53f,Ivory);
    };
    Ability(W-219*S,H-111*S,39*S,CharmIcon,TEXT("LMB"),TEXT("CHARM STRIKE"),Hero->AttackCooldownRemaining(),.75f);
    Ability(W-96*S,H-139*S,53*S,SealIcon,TEXT("Q"),TEXT("SPIRIT SEAL"),Hero->SkillCooldownRemaining(),6.f);

    if(Hero->HasMoveDestination()) {
        FVector2D P;
        if(GetOwningPlayerController()->ProjectWorldLocationToScreen(Hero->GetMoveDestination()-FVector(0,0,80),P)) {
            Ring(P.X,P.Y,10*S,FLinearColor(.84f,.91f,.74f,.8f));
            Diamond(P.X,P.Y,17*S,Gold);
        }
    }
}
