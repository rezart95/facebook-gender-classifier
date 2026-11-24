"""The 31 dictionary patterns published in myFBr (R/utils_messages.R), in 2019 column order.

Translated from R/ICU to Python `re`: `[[:blank:]]` became `[ \t]`; everything else is
verbatim, including the 2019 quirks: mis-encoded characters (Ã¹, Ã§, Ã²) that never match
real text, `<U+2764>` written as literal text, and EMOTEUHUH duplicating EMOTEIHIH.
"""

from __future__ import annotations

MYFBR_PATTERNS: tuple[tuple[str, str], ...] = (
    ("domanda", r"\?"),
    ("esclamativo", r"\!"),
    ("virgole_punti", r"(,|;|\.)"),
    (
        "EMOTEGOOD",
        r"\:\)+|\:\-\)+|\:\]+|\:\-\]+|\=\)+|\=\]+|\=\>|\:\>|\^\^|\^\_+\^|\^\-\^|\^o\^"
        r"|\:[ \t]\)+|[ \t]\([ \t]?\:|\:\'D+",
    ),
    ("EMOTELOVE", r"\<3+|<U+2764>|<U+2665>|\:\*+"),
    (
        "EMOTEBAD",
        r"\:\(+|\:\-\(+|\:\[+|\:\-\[+|\=\[+|\=\(+|\:[ \t]\(|[ \t]\([ \t]?\:|\:\'+\(+"
        r"|\:\'\[|D\:|\:\-\[|\:\|\:/+|\=/+|\:x|\#\_+\#|X\_+X|x\_+x|X\.X|x\.x|>\.<"
        r"|>\_+<|>\_+>|>\.>",
    ),
    ("EMOTEWINK", r"\;\)+|\;\-\)+|\;\]|\;\-\]|\;\>|;d+|;D+|;o"),
    (
        "EMOTESHOCK",
        r"O\.o|o\.o|O\.O|o\.O|O\_+o|o\_+o|O\_+O|o\_+O|\:OO+|\=O+|\-\.\-|u\.u"
        r"|u\.Ã¹|Ã¹\.u|u\_+u|Ã§Ã§|Ã§_+Ã§|t_+t|Ã¹\_+Ã¹|Ã¹\.Ã¹|\:oo+|0\_+0|\=\_+\="
        r"|\.\_+\.|Ã²Ã²|Ã²\_+Ã²|\*u+\*|\-\_+\-|Ã¹Ã¹|\-\,\-|\-\-\'|\.\-\.|\'\-\'",
    ),
    (
        "EMOTEAMAZE",
        r"\:P+[^e]|\:p+[^e]|\=P+|\=p+|XD+|xD+|xd+|[ \t]d\:|\:P+[^e]|\:p+[^e]|\=P+"
        r"|\=p+|XD+|xD+|xd+|[ \t]d\:",
    ),
    ("EMOTEZZZ", r"(#?zz+|#?u+ff[aif]+?|#?r+o+n+f+|#uff|ronf)"),
    ("EMOTESIII", "(#?sii+|#si+|#?yes+|#?s\uc38c\uc38c+)"),
    ("EMOTENOOO", r"(#?noo+|#no+|#?nuu+)"),
    ("EMOTEAHHH", r"(#?ahh+)"),
    ("EMOTEEHHH", r"(#?ehh+)"),
    ("EMOTEOHOH", r"(#?o?h?o+h[oh]+)"),
    ("EMOTEIHIH", r"(#?i?h?i+h[ih]+)"),
    ("EMOTEUHUH", r"(#?i?h?i+h[ih]+)"),
    ("EMOTEAHAH", r"(#?a?h?ah[^h][ah]+)"),
    ("EMOTEEHEH", r"(#?e?h?eh[^h][eh]+)"),
    ("EMOTEAZZ", r"(#?azz+)"),
    ("EMOTEDAIII", r"(#?[dv]aii+|#[dv]ai|forzaa+)"),
    ("cazzo", r"(#?cazz[oi]+|ca\*\*o|c\*\*\*+o)"),
    ("cazzata", r"(#?cazzat[a]+)"),
    ("merda", r"(#?merd[a]+)"),
    ("EMOTEAAA", r"(#?aaa+)"),
    ("EMOTEOOO", r"(#?ooo+)"),
    ("EMOTEEEE", r"(#?eee+)"),
    ("EMOTELOL", r"(#?l+o+l+|#?r+o+f+t+l+)"),
    ("EMOTESOS", r"(#?aiutoo+|#?sos|#?help+)"),
    ("EMOTEBASTA", r"(#ba+sta+|ba+staa+)"),
    ("EMOTEWOW", r"#?([uw]+[ao]+[uw]+)"),
)
