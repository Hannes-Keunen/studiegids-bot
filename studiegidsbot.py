from keras.models import load_model
model = load_model('chatbot_model.h5')
import random
import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import json
import pickle
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl','rb'))
classes = pickle.load(open('classes.pkl','rb'))
import numpy as np

import course_api as api


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))


def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def get_response(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result


courses = None
course_infos = {}
last_course = None

def lookup_course(msg):
    global courses
    global course_infos
    global last_course

    if courses is None:
        courses = api.list_all_courses()

    searchmsg = msg.strip().casefold()
    
    course_id = ''
    for course in courses:
        if searchmsg.find(course['searchname']) != -1:
            course_id = course['id']
    
    if course_id == '':
        result = last_course
    elif course_id in course_infos:
        result = course_infos[course_id]
    else:
        info = api.parse_course(course_id)
        course_infos[course_id] = info
        result = info

    last_course = result
    return result


def init():
    """
    Pre-load the list of courses
    """
    courses = api.list_all_courses()


taken_courses = []


def chatbot_response(msg):
    ints = predict_class(msg, model)
    tag = ints[0]['intent']

    # Inhoud van een vak opvragen
    if tag == 'content':
        course = lookup_course(msg)
        if course is None:
            res = 'Dat vak ken ik niet! Zeker dat je het juist hebt geschreven?'
        else:
            res = 'Dit is wat ik hierover kan vinden in de studiegids:\n\t%s' % course.content

    # Prof opvragen
    elif tag == 'lecturer':
        course = lookup_course(msg)
        if course is None:
            res = 'Dat vak ken ik niet! Zeker dat je het juist hebt geschreven?'
        else:
            res = course.education_team[0]['name']

    # Vak opnemen
    elif tag == 'take':
        course = lookup_course(msg)
        already_taken = False
        for c in taken_courses:
            if c.id == course.id:
                res = 'Als ik het me goed herinner heb je dat vak al opgenomen!'
                already_taken = True
                break
        if not already_taken:
            taken_courses.append(course)
            res = '%s opnemen? Staat genoteerd!' % course.name

    # Vak laten vallen
    elif tag == 'drop':
        course = lookup_course(msg)
        deleted = False
        for c in taken_courses:
            if c.id == course.id:
                taken_courses.remove(course)
                deleted = True
                res = 'Okay, dan heb je nu nog ?? studiepunten over!'
                break
        if not deleted:
            res = 'Ik kan me niet herinneren dat je dat vak had opgenomen!'

    # Totaal aantal studiepunten opvragen
    elif tag == 'total_credits':
        credits = credits_p1 = credits_p2 = 0
        for course in taken_courses:
            credits += course.creditsof
            if course.semester == 1:
                credits_p1 += course.credits
            elif course.semester == 2:
                credits_p2 += course.credits
        if credits == 0:
            res = "Neem eerst maar wat vakken op, dan kan ik je exact vertellen hoeveel studiepunten je hebt ;-)"
        else:
            res = "Je hebt in totaal %d studiepunten opgenomen. Dat zijn er %d in het eerste semester en %d in het tweede!" % (credits, credits_p1, credits_p2)
    
    # Eenvoudige antwoorden
    else:
        res = get_response(ints, intents)
    return res


if __name__ == "__main__":
    print("Start talking with the bot! (type quit to stop)")
    while True:
        inp = input("You: ")
        if inp.lower() == "quit":
            break

        result = chatbot_response(inp)
        print(result)
