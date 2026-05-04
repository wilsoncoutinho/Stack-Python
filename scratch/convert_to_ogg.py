import os
import soundfile as sf

ASSETS_SOUNDS = os.path.join("assets", "sounds")

def convert_wav_to_ogg():
    files = [f for f in os.listdir(ASSETS_SOUNDS) if f.endswith(".wav")]
    if not files:
        print("No .wav files found in " + ASSETS_SOUNDS)
        return

    for filename in files:
        wav_path = os.path.join(ASSETS_SOUNDS, filename)
        ogg_filename = filename.replace(".wav", ".ogg")
        ogg_path = os.path.join(ASSETS_SOUNDS, ogg_filename)
        
        print(f"Converting {filename} to {ogg_filename}...")
        try:
            data, samplerate = sf.read(wav_path)
            sf.write(ogg_path, data, samplerate, format='OGG', subtype='VORBIS')
            os.remove(wav_path)
            print(f"  Successfully converted and removed original.")
        except Exception as e:
            print(f"  Error converting {filename}: {e}")

if __name__ == "__main__":
    convert_wav_to_ogg()
