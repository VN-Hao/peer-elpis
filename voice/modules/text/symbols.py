"""Text symbols for OpenVoice."""

# Special symbol ids
SPECIAL_SYMBOLS = ['', '|', '||']

# IPA vowels and consonants (basic set)
IPA_VOWELS = ['i', 'y', 'ɨ', 'ʉ', 'ɯ', 'u', 'ɪ', 'ʏ', 'ʊ', 'e', 'ø', 'ɘ', 'ɵ', 'ɤ', 'o', 'ə', 'ɛ', 'œ', 'ɜ', 'ɞ', 'ʌ', 'ɔ', 'æ', 'ɐ', 'a', 'ɶ', 'ɑ', 'ɒ']
IPA_CONSONANTS = ['b', 'd', 'ð', 'ɖ', 'f', 'g', 'h', 'j', 'k', 'l', 'ɭ', 'm', 'n', 'ɳ', 'ŋ', 'p', 'r', 's', 'ʃ', 't', 'v', 'w', 'x', 'z', 'ʒ', 'θ', 'ʔ', 'ɹ']

# IPA diacritics and modifiers
IPA_MODIFIERS = ['ː', 'ˈ', 'ˌ', '̃', '̊', '̥', '̰', '̩', '̍']

# Chinese pinyin
PINYIN = ['ā', 'á', 'ǎ', 'à', 'ē', 'é', 'ě', 'è', 'ī', 'í', 'ǐ', 'ì', 'ō', 'ó', 'ǒ', 'ò', 'ū', 'ú', 'ǔ', 'ù', 'ǖ', 'ǘ', 'ǚ', 'ǜ']

# Basic latin alphabet
LATIN = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

# Combine all symbols
symbols = (
    SPECIAL_SYMBOLS +
    IPA_VOWELS + 
    IPA_CONSONANTS + 
    IPA_MODIFIERS +
    PINYIN + 
    LATIN
)
