import React from 'react';
import ReactDOM from 'react-dom/client';
import QuizPlayer from './QuizPlayer';

// On cherche le conteneur spécifique au quiz
const quizRoot = document.getElementById('react-quiz-root');

if (quizRoot) {
  ReactDOM.createRoot(quizRoot).render(
    <React.StrictMode>
      <QuizPlayer />
    </React.StrictMode>
  );
}