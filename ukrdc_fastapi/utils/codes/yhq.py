from typing import TypedDict


class MetaDataItem(TypedDict):
    group: str
    question: str
    answers: dict[str, str]


MetadataTypeAlias = dict[str, MetaDataItem]

METADATA: MetadataTypeAlias = {
    "MYHQ1": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "When all is said and done, I am the person who is "
        "responsible for taking care of my health.",
    },
    "MYHQ10": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident that I can tell a doctor or nurse "
        "specialist concerns I have even when he or she does "
        "not ask.",
    },
    "MYHQ11": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident that I can follow through on medical "
        "treatments I may need to do at home.",
    },
    "MYHQ12": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I understand my health problems and what causes " "them.",
    },
    "MYHQ13": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident I can maintain lifestyle changes, like "
        "eating right and exercising, even during times of "
        "stress.",
    },
    "MYHQ2": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "Taking an active role in my own health care is the "
        "most important thing that affects my health.",
    },
    "MYHQ3": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident I can help prevent or reduce problems "
        "associated with my health.",
    },
    "MYHQ4": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I know what each of my prescribed medications do.",
    },
    "MYHQ5": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident that I can tell whether I need to go to "
        "the doctor or whether I can take care of a health "
        "problem myself.",
    },
    "MYHQ6": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I have been able to maintain (keep up with) lifestyle "
        "changes, like eating right or exercising.",
    },
    "MYHQ7": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I am confident I can work out solutions when new "
        "problems arise with my health.",
    },
    "MYHQ8": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I know how to prevent problems with my health.",
    },
    "MYHQ9": {
        "answers": {
            "1": "Strongly Disagree",
            "2": "Disagree",
            "3": "Agree",
            "4": "Strongly Agree",
            "5": "N/A",
        },
        "group": "Patient Activation",
        "question": "I know what treatments are available for my health " "problems.",
    },
    "YOHQ1": {
        "answers": {
            "1": "I have no problems in walking about",
            "2": "I have slight problems in walking about",
            "3": "I have moderate problems in walking about",
            "4": "I have severe problems in walking about",
            "5": "I am unable to walk about",
        },
        "group": "EQ5D",
        "question": "Mobility",
    },
    "YOHQ2": {
        "answers": {
            "1": "I have no problems washing or dressing myself",
            "2": "I have slight problems washing or dressing myself",
            "3": "I have moderate problems washing or dressing " "myself",
            "4": "I have severe problems washing or dressing myself",
            "5": "I am unable to wash or dress myself",
        },
        "group": "EQ5D",
        "question": "Self-care",
    },
    "YOHQ3": {
        "answers": {
            "1": "I have no problems doing my usual activities",
            "2": "I have slight problems doing my usual activities",
            "3": "I have moderate problems doing my usual " "activities",
            "4": "I have severe problems doing my usual activities",
            "5": "I am unable to do my usual activities",
        },
        "group": "EQ5D",
        "question": "Usual Activities",
    },
    "YOHQ4": {
        "answers": {
            "1": "I have no pain or discomfort",
            "2": "I have slight pain or discomfort",
            "3": "I have moderate pain or discomfort",
            "4": "I have severe pain or discomfort",
            "5": "I have extreme pain or discomfort",
        },
        "group": "EQ5D",
        "question": "Pain / Discomfort",
    },
    "YOHQ5": {
        "answers": {
            "1": "I am not anxious or depressed",
            "2": "I am slightly anxious or depressed",
            "3": "I am moderately anxious or depressed",
            "4": "I am severely anxious or depressed",
            "5": "I am extremely anxious or depressed",
        },
        "group": "EQ5D",
        "question": "Anxiety / Depression",
    },
    "YSQ1": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Pain",
    },
    "YSQ10": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Poor mobility",
    },
    "YSQ11": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Itching",
    },
    "YSQ12": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Difficulty sleeping",
    },
    "YSQ13": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Restless legs or difficulty keeping legs still",
    },
    "YSQ14": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Changes in skin",
    },
    "YSQ15": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Diarrhoea",
    },
    "YSQ16": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Feeling anxious or worried about your illness or " "treatment",
    },
    "YSQ17": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Feeling depressed",
    },
    "YSQ2": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Shortness of breath",
    },
    "YSQ3": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Weakness or lack of energy",
    },
    "YSQ4": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Nausea (feeling like you are going to be sick)",
    },
    "YSQ5": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Vomiting (being sick)",
    },
    "YSQ6": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Poor appetite",
    },
    "YSQ7": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Constipation",
    },
    "YSQ8": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Sore or dry mouth",
    },
    "YSQ9": {
        "answers": {
            "1": "Not at all",
            "2": "Slightly",
            "3": "Moderately",
            "4": "Severely",
            "5": "Overwhelmingly",
        },
        "group": "Patient Reported Outcome Measures",
        "question": "Drowsiness",
    },
}
