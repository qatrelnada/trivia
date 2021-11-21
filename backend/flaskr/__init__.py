import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @DONE: Set up CORS. Allow '*' for origins.
    Delete the sample route after completing the TODOs
    '''
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
    @DONE: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()

        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': {category.format()['id']: category.format()['type']
                           for category in categories}
        })

    @app.route('/questions')
    def get_paginated_questions():
        categories = Category.query.order_by(Category.id).all()
        selection = Question.query.order_by(Question.id).all()

        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': None,
            'categories': {category.format()['id']: category.format()['type']
                           for category in categories}
            })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id
                ).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
                )

            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()

        search = body.get('searchTerm', None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search))
                    )
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all())
                })

        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        selection = Question.query.filter(
            Question.category == category_id
            ).all()
        current_questions = paginate_questions(request, selection)

        if not selection:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': Category.query.filter(
                Category.id == category_id
                ).one_or_none().format()
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        if body:
            category = body.get('category', None)
            previous_questions = body.get('previous_questions', None)
            if category:
                questions = Question.query.filter(
                    Question.category == category,
                    Question.id.notin_(previous_questions)
                ).all()

            else:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)
                    ).all()

            random_question = random.choice(questions)
            return jsonify({
                "success": True,
                "question": random_question.format()
            })

        else:
            abort(404)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def server_side_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Server side error"
        }), 500

    return app
