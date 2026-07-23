import { useState } from "react";
import { Check, X } from "lucide-react";
import type { QuizResponse } from "../types/api";

export function QuizPanel({ quiz }: { quiz: QuizResponse }) {
  const [answers, setAnswers] = useState<Record<number, number>>({});

  const selectAnswer = (questionIndex: number, optionIndex: number) => {
    if (answers[questionIndex] !== undefined) return; // locked once answered
    setAnswers((prev) => ({ ...prev, [questionIndex]: optionIndex }));
  };

  const score = Object.entries(answers).filter(
    ([qIdx, aIdx]) => quiz.questions[Number(qIdx)].correct_index === aIdx
  ).length;
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="flex flex-col gap-5">
      {answeredCount === quiz.questions.length && quiz.questions.length > 0 && (
        <div className="rounded-lg bg-rose-500/10 px-3.5 py-2.5 text-center text-sm font-medium text-rose-400">
          {score} / {quiz.questions.length} correct
        </div>
      )}

      {quiz.questions.map((q, qIdx) => {
        const selected = answers[qIdx];
        const isAnswered = selected !== undefined;

        return (
          <div key={qIdx} className="rounded-lg border border-ink-600 p-4">
            <p className="mb-3 text-sm font-medium text-paper-100">
              {qIdx + 1}. {q.question}
            </p>
            <div className="flex flex-col gap-2">
              {q.options.map((option, oIdx) => {
                const isCorrect = oIdx === q.correct_index;
                const isSelected = oIdx === selected;

                let stateClasses = "border-ink-600 hover:border-ink-500";
                if (isAnswered) {
                  if (isCorrect) stateClasses = "border-sage-500 bg-sage-500/10";
                  else if (isSelected) stateClasses = "border-crimson-500 bg-crimson-500/10";
                }

                return (
                  <button
                    key={oIdx}
                    onClick={() => selectAnswer(qIdx, oIdx)}
                    disabled={isAnswered}
                    className={`flex items-center justify-between rounded-lg border px-3 py-2 text-left text-sm text-paper-100 transition-colors disabled:cursor-default ${stateClasses}`}
                  >
                    {option}
                    {isAnswered && isCorrect && <Check size={14} className="text-sage-400" />}
                    {isAnswered && isSelected && !isCorrect && <X size={14} className="text-crimson-400" />}
                  </button>
                );
              })}
            </div>
            {isAnswered && q.explanation && (
              <p className="mt-3 text-xs text-paper-300">{q.explanation}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
