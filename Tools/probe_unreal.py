import unreal as u
from pathlib import Path
p=Path('G:/Code/UE/Research/unreal_api.txt')
names=['BlendableLocation','SceneTextureId','CustomMaterialOutputType','CollectionScalarParameter','MaterialParameterCollection','FbxStaticMeshImportData','MaterialExpressionCustom','MaterialExpressionCollectionParameter','MaterialExpressionSceneTexture','SkyLightComponent','PostProcessSettings','StaticMeshEditorSubsystem']
with p.open('w',encoding='utf8') as f:
    for name in names:
        cls=getattr(u,name,None)
        f.write('\n'+name+'\n'+str(cls.__doc__ if cls else None)+'\n')
        if cls: f.write(str([i for i in dir(cls) if not i.startswith('_')])+'\n')
u.log('PROBE_DONE')
