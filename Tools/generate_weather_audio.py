"""Synthesize three original looping ambience beds for the weather system."""
from pathlib import Path
import wave
import numpy as np

out=Path('EternalRebirth/SourceArt/Weather')
out.mkdir(parents=True,exist_ok=True)
rate=32000
seconds=8
count=rate*seconds
t=np.arange(count,dtype=np.float64)/rate
rng=np.random.default_rng(30058)


def filtered_noise(low,high,tilt=0):
    source=rng.normal(size=count)
    spectrum=np.fft.rfft(source)
    frequencies=np.fft.rfftfreq(count,1/rate)
    band=(frequencies>=low)&(frequencies<=high)
    weight=np.zeros_like(frequencies)
    weight[band]=np.maximum(frequencies[band],20)**(-tilt)
    signal=np.fft.irfft(spectrum*weight,n=count)
    return signal/(np.std(signal)+1e-9)


def droplet_track(number):
    track=np.zeros(count)
    for start in rng.integers(0,count-2000,size=number):
        length=int(rng.integers(200,1000))
        local=np.arange(length)/rate
        freq=rng.uniform(750,2700)
        kernel=np.sin(2*np.pi*freq*local)*np.exp(-local*rng.uniform(95,180))
        track[start:start+length]+=kernel*rng.uniform(.18,.55)
    return track


def bird_track():
    track=np.zeros(count)
    for start_time in (1.0,1.35,3.8,4.15,6.4,6.73):
        length=int(.15*rate)
        local=np.arange(length)/rate
        frequency=850+420*np.sin(np.pi*local/.15)
        phase=np.cumsum(2*np.pi*frequency/rate)
        shape=np.sin(np.pi*local/.15)**2
        start=int(start_time*rate)
        track[start:start+length]+=.16*np.sin(phase)*shape
    return track


rain_base=.16*filtered_noise(80,11000,.16)+.18*filtered_noise(500,13000,0)
rain=rain_base+.09*droplet_track(420)
rain*=.80+.20*np.sin(2*np.pi*(2/seconds)*t)

snow=.16*filtered_noise(35,700,.53)+.07*filtered_noise(450,1800,.25)
snow*=.58+.42*np.sin(2*np.pi*(1/seconds)*t+.6)**2
snow_phase=np.cumsum(2*np.pi*(410+35*np.sin(2*np.pi*t/seconds))/rate)
snow+=.012*np.sin(snow_phase)

clear=.08*filtered_noise(55,1600,.38)+bird_track()
clear*=.78+.22*np.sin(2*np.pi*(1/seconds)*t)


def write(name,mono):
    # The FFT beds and modulations cover whole cycles, so the loop joins
    # continuously without a brief drop in volume every eight seconds.
    stereo=np.column_stack((mono,mono*.96+np.roll(mono,71)*.04))
    stereo=np.clip(stereo,-.92,.92)
    path=out/(name+'.wav')
    with wave.open(str(path),'wb') as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes((stereo*32767).astype('<i2').tobytes())
    print(path,round(float(np.sqrt(np.mean(stereo**2))),3))


write('ClearAmbience',clear)
write('RainAmbience',rain)
write('SnowAmbience',snow)
