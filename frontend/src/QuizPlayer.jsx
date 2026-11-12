import React, { useState, useEffect } from 'react';

export default function QuizPlayer() {
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isFinished, setIsFinished] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState({ score: 0, max_score: 0 });
  const [activityId, setActivityId] = useState(null);

  useEffect(() => {
    // On récupère les données JSON passées par Django
    const dataScript = document.getElementById('quiz-data');
    if (dataScript) {
      setQuestions(JSON.parse(dataScript.textContent));
    }
    
    const rootElement = document.getElementById('react-quiz-root');
    if (rootElement) {
      setActivityId(rootElement.dataset.activityId);
    }
  }, []);

  const handleChoiceSelect = (questionId, choiceId) => {
    setAnswers(prev => ({ ...prev, [questionId]: choiceId }));
  };

  // Fonction pour récupérer le token CSRF de Django
  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const csrfToken = getCookie('csrftoken');
    
    try {
      const response = await fetch(`/eleve/api/quiz/${activityId}/submit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ answers })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setResult({ score: data.score, max_score: data.max_score });
        setIsFinished(true);
      } else {
        alert("Une erreur est survenue lors de l'envoi du quiz.");
      }
    } catch (error) {
      console.error("Erreur réseau", error);
      alert("Erreur de connexion au serveur.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (questions.length === 0) return <div className="text-center p-5">Chargement du quiz...</div>;

  if (isFinished) {
    const percentage = (result.score / result.max_score) * 100;
    const scoreColor = percentage >= 70 ? 'text-success' : (percentage >= 50 ? 'text-warning' : 'text-danger');
    
    return (
      <div className="card shadow-sm border-0 p-5 text-center" style={{ borderRadius: '12px' }}>
        <h2 className="fw-bold mb-4">Quiz terminé !</h2>
        <div className={`display-1 fw-bold ${scoreColor} mb-3`}>
          {result.score} / {result.max_score}
        </div>
        <p className="text-muted mb-4">Votre score a bien été enregistré.</p>
        <div className="d-flex justify-content-center gap-3">
           <a href="javascript:history.back()" className="btn btn-outline-secondary rounded-pill px-4">
             Retour
           </a>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="card shadow-sm border-0 p-4" style={{ borderRadius: '12px' }}>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h5 className="fw-bold text-muted mb-0">Question {currentQuestionIndex + 1} / {questions.length}</h5>
      </div>

      <h4 className="fw-bold mb-4">{currentQuestion.text}</h4>

      <div className="d-flex flex-column gap-3 mb-4">
        {currentQuestion.choices.map((choice) => {
          const isSelected = answers[currentQuestion.id] === choice.id;
          return (
            <button
              key={choice.id}
              onClick={() => handleChoiceSelect(currentQuestion.id, choice.id)}
              className={`btn text-start p-3 ${isSelected ? 'btn-primary' : 'btn-outline-secondary'}`}
              style={{ borderRadius: '12px', transition: 'all 0.2s' }}
            >
              {choice.text}
            </button>
          );
        })}
      </div>

      <div className="d-flex justify-content-between mt-4 border-top pt-3">
        <button 
          className="btn btn-outline-secondary rounded-pill" 
          onClick={() => setCurrentQuestionIndex(currentQuestionIndex - 1)}
          disabled={currentQuestionIndex === 0 || isSubmitting}
        >
          Précédent
        </button>

        {currentQuestionIndex < questions.length - 1 ? (
          <button 
            className="btn btn-primary rounded-pill px-4" 
            onClick={() => setCurrentQuestionIndex(currentQuestionIndex + 1)}
            disabled={!answers[currentQuestion.id] || isSubmitting}
          >
            Suivant
          </button>
        ) : (
          <button 
            className="btn btn-success rounded-pill px-4" 
            onClick={handleSubmit}
            disabled={!answers[currentQuestion.id] || isSubmitting}
          >
            {isSubmitting ? 'Envoi en cours...' : 'Terminer le quiz'}
          </button>
        )}
      </div>
    </div>
  );
}