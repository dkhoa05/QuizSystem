from app import create_app, db
from app.models import User, Quiz, Question, Choice, Submission, Answer

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Quiz": Quiz,
        "Question": Question,
        "Choice": Choice,
        "Submission": Submission,
        "Answer": Answer,
    }


if __name__ == "__main__":
    app.run()
