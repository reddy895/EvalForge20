import React from 'react';
import { Check, ChevronRight } from 'lucide-react';
import './EvalWizard.css';

export interface WizardStep {
  id: number;
  label: string;
  shortTitle: string;
}

export const WIZARD_STEPS: WizardStep[] = [
  { id: 1, label: 'Select Dataset', shortTitle: 'Dataset' },
  { id: 2, label: 'Target Model & Provider', shortTitle: 'Provider' },
  { id: 3, label: 'Model Configuration', shortTitle: 'Parameters' },
  { id: 4, label: 'Evaluators & Metrics', shortTitle: 'Evaluators' },
  { id: 5, label: 'Execution Controls', shortTitle: 'Execution' },
  { id: 6, label: 'Review & Launch', shortTitle: 'Review' },
];

interface WizardHeaderProps {
  currentStep: number;
  onStepClick: (step: number) => void;
  maxStepReached: number;
}

export const WizardHeader: React.FC<WizardHeaderProps> = ({
  currentStep,
  onStepClick,
  maxStepReached,
}) => {
  return (
    <nav className="wizard-steps-header" aria-label="Evaluation Wizard Steps">
      {WIZARD_STEPS.map((step, idx) => {
        const isCompleted = step.id < currentStep;
        const isActive = step.id === currentStep;
        const isClickable = step.id <= maxStepReached && !isActive;

        return (
          <React.Fragment key={step.id}>
            <div
              className={`wizard-step-item ${isActive ? 'active' : ''} ${
                isCompleted ? 'completed' : ''
              }`}
              onClick={() => isClickable && onStepClick(step.id)}
              role={isClickable ? 'button' : undefined}
              tabIndex={isClickable ? 0 : undefined}
            >
              <div className="wizard-step-number">
                {isCompleted ? <Check size={11} /> : step.id}
              </div>
              <span>{step.label}</span>
            </div>
            {idx < WIZARD_STEPS.length - 1 && (
              <span className="wizard-step-separator" aria-hidden="true">
                <ChevronRight size={12} />
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
