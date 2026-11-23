import argostranslate.package as package
import argostranslate.translate as translate
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier

from translator import PAIRS


def main():
    installed = {language.code for language in translate.get_installed_languages()}
    if not all(code in installed for pair in PAIRS for code in pair):
        package.update_package_index()
        for available in package.get_available_packages():
            if (available.from_code, available.to_code) in PAIRS:
                package.install_from_path(available.download())

    WhisperModel("base", device="cpu", compute_type="int8")
    EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
    print("Modelos descargados y listos.")


if __name__ == "__main__":
    main()
