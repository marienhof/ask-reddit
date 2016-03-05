import argparse
import readline

import language
import sentence2vec

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from termcolor import colored


PROJECT_ID = "reddit-1239"

TABLE_NAME = "%s:reddit_subset.posts_with_responses_sc_cnt_norm" % PROJECT_ID

MAX_RESULTS_PER_QUESTION = 30


def sql_contains(field_name, s):
    return ' ((%s CONTAINS "%s ") OR (%s CONTAINS " %s"))' % (field_name, s, field_name, s)


def generate_sql(table_name, question_words, only_questions):
    sql = 'SELECT * FROM [%s] WHERE ' % table_name
    sql += ' AND '.join([sql_contains('post_title_lower', word) for word in question_words])
    sql += ' AND response_body_lower != "[deleted]" '
    if only_questions:
        sql += ' AND RIGHT(RTRIM(response_body_lower), 1) = "?"'
    sql += ' ORDER BY cnt LIMIT 10000;'
    return sql


def execute_query(bigquery_service, question, only_questions=False):
    words = language.filter_stopwords(language.sentence_to_words(question))    
    try:
        query_request = bigquery_service.jobs()
        query_sql = generate_sql(TABLE_NAME, words, only_questions)
        query_data = { 'query': query_sql }
        query_response = query_request.query(
            projectId=PROJECT_ID,
            body=query_data).execute()
    except HttpError as err:
        print('Error: {}'.format(err.content))
        raise err
    else:
        results = []
        field_names = ["question", "answer", "count", "score"]
        if 'rows' not in query_response:
            return []
        for row in query_response['rows']:
            result = {
                "is_nasty": False
            }
            for (field_name, field) in zip(field_names, row['f']):
                value = language.clean(field['v'])
                result["is_nasty"] = language.is_nasty(value) or result["is_nasty"]
                result[field_name] = value
            result["question_similarity"] = sentence2vec.similarity(question, result["question"])
            if (not result["is_nasty"]) and result["question_similarity"] > -.4:
                results.append(result)
        return results


def sort_score(x):
    # TODO: adjust parameters
    return -(x["question_similarity"] + max(float(x["score"]) / 500.0, .2))


def print_results(question, results):
    for result in sorted(results, key=sort_score)[:MAX_RESULTS_PER_QUESTION]:
        question = result['question']
        answer = result['answer']
        question_similarity = result['question_similarity']
        score = result['score']
        print ("=> " + colored(answer, 'yellow') +
               " (" + question + ") " +
               colored("{0:.2f}".format(round(question_similarity, 2)), 'green') + ' ' +
               colored(score, 'red'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", help="only show follow-up questions", action="store_true")
    args = parser.parse_args()    
    credentials = GoogleCredentials.get_application_default()
    bigquery_service = build('bigquery', 'v2', credentials=credentials)
    while True:
        try:
            question = raw_input('?> ')
            results = execute_query(bigquery_service, question, only_questions=args.questions)
        except KeyboardInterrupt:
            break
        else:
            print_results(question, results[:100])
            print


if __name__ == '__main__':
    main()
