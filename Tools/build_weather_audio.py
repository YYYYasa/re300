"""Import the seamless clear, rain and snow ambience loops."""
from pathlib import Path
import unreal as u

assets=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
audio_folder='/Game/Art/Audio'
assets.make_directory(audio_folder)
root=Path('G:/Code/UE/EternalRebirth/SourceArt/Weather')
names=(('ClearAmbience','ClearWeatherLoop'),
       ('RainAmbience','RainWeatherLoop'),
       ('SnowAmbience','SnowWeatherLoop'))
tasks=[]
for source_name,asset_name in names:
    source=root/(source_name+'.wav')
    if not source.is_file():
        raise RuntimeError('Missing generated audio: '+str(source))
    task=u.AssetImportTask()
    task.filename=str(source)
    task.destination_path=audio_folder
    task.destination_name=asset_name
    task.automated=True
    task.save=True
    task.replace_existing=True
    tasks.append(task)
tools.import_asset_tasks(tasks)
for _,asset_name in names:
    sound=u.load_asset(audio_folder+'/'+asset_name)
    if not isinstance(sound,u.SoundWave):
        raise RuntimeError('Audio import failed: '+asset_name)
    sound.set_editor_property('looping',True)
    if not assets.save_loaded_asset(sound,False):
        raise RuntimeError('Could not save looping audio: '+asset_name)
u.log('REBIRTH: WEATHER_AUDIO_COMPLETE assets=3')
