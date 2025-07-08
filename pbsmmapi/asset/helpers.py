from datetime import datetime

from dateutil import parser
from nltk import PunktSentenceTokenizer
from pycaption.base import (
    BaseWriter,
    CaptionNode,
)
import pytz


def check_asset_availability(start=None, end=None):
    """
    Am I within the Asset's availablity window?

    If "start" is defined,  now >= start must be True
    If "end" is defined, now <= end must be True.

    Otherwise each condition is presumed TRUE
        (e.g., no "end" date means that it doesn't expire, hence "True")

    Returns a 3-ple:
        0: True or False
        1: A code  -1 = unknown, 0 = not-yet-available, 1 = available, 2 = expired
        2: the text associated with the code (see previous line)
    """
    now = datetime.now(pytz.utc)

    if start:
        start_date = parser.parse(start)
    if end:
        end_date = parser.parse(end)

    if start and now < start_date:
        return (False, 0, "not-yet-available")
    if end is None or now <= end_date:
        return (True, 1, "available")
    if end and now > end_date:
        return (False, 2, "expired")

    return (False, -1, "unknown")


class SafeTranscriptWriter(BaseWriter):
    """
    Adapted from pycaption.transcript.TranscriptWriter, using safe nltk version.
    """

    def __init__(self, *args, **kwargs):
        self.tokenizer = PunktSentenceTokenizer()
        super().__init__(*args, **kwargs)

    def write(self, captions):
        transcripts = []

        for lang in captions.get_languages():
            lang_transcript = ""

            for caption in captions.get_captions(lang):
                lang_transcript = self._strip_text(caption.nodes, lang_transcript)

            lang_transcript = "\n".join(self.tokenizer.tokenize(lang_transcript))
            transcripts.append(lang_transcript)

        return "\n".join(transcripts)

    def _strip_text(self, elements, lang_transcript):
        return " ".join(
            [lang_transcript]
            + [el.content for el in elements if el.type_ == CaptionNode.TEXT]
        )
