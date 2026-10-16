import React, { useState } from 'react';
import { Play, ArrowLeft, ArrowRight, ShieldCheck, AlertOctagon } from 'lucide-react';
import { api } from '../api/client';
import type { TargetConfiguration, EvaluatorConfiguration } from '../api/types';
import { type NavRoute } from '../types/navigation';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { WizardHeader } from '../components/eval-flow/EvalWizard';
import { StepDataset } from '../components/eval-flow/StepDataset';
import { StepProvider } from '../components/eval-flow/StepProvider';
import { StepEvaluators } from '../components/eval-flow/StepEvaluators';
import './NewEvalPage.css';

interface NewEvalPageProps {
  onNavigate: (route: NavRoute, runId?: string) => void;
}

export const NewEvalPage: React.FC<NewEvalPageProps> = ({ onNavigate }) => {
  const toast = useToast();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [maxStepReached, setMaxStepReached] = useState<number>(1);

  // Form State
  const [runName, setRunName] = useState<string>('Evaluation Run — ' + new Date().toISOString().substring(0, 10));
  const [datasetPath, setDatasetPath] = useState<string | null>('examples/datasets/basic.jsonl');
  const [datasetContent, setDatasetContent] = useState<string | null>(null);
  const [target, setTarget] = useState<TargetConfiguration>({
    target_name: 'ollama-qwen2.5-3b',
    target_type: 'ollama',
    provider_name: 'ollama',
    model_identifier: 'qwen2.5:3b',
    base_url: 'http://localhost:11434',
    temperature: 0.0,
    max_tokens: null,
    timeout_seconds: 60.0,
    extra_params: {},
  });
  const [evaluators, setEvaluators] = useState<EvaluatorConfiguration[]>([
    { evaluator_name: 'Exact Match', metric_id: 'exact_match', weight: 1.0 },
    { evaluator_name: 'Normalized Match', metric_id: 'normalized_match', weight: 1.0 },
  ]);
  const [concurrency, setConcurrency] = useState<number>(5);
  const [retries, setRetries] = useState<number>(2);

  // Step Validation States
  const [step1Valid, setStep1Valid] = useState<boolean>(true);
  const [step2Valid, setStep2Valid] = useState<boolean>(true);
  const [step4Valid, setStep4Valid] = useState<boolean>(true);

  // Execution States
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionError, setExecutionError] = useState<string | null>(null);

  const goToStep = (step: number) => {
    setCurrentStep(step);
    if (step > maxStepReached) setMaxStepReached(step);
  };

  const handleNext = () => {
    if (currentStep < 6) {
      goToStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      goToStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return step1Valid;
      case 2:
      case 3:
        return step2Valid;
      case 4:
        return step4Valid;
      case 5:
        return Boolean(runName.trim() && concurrency >= 1);
      default:
        return true;
    }
  };

  const handleLaunchEvaluation = async () => {
    setIsExecuting(true);
    setExecutionError(null);

    try {
      const payload = {
        name: runName.trim(),
        dataset_path: datasetPath,
        dataset_content: datasetContent,
        target,
        evaluators,
        max_concurrency: concurrency,
        max_retries: retries,
        timeout_seconds: target.timeout_seconds,
      };

      const result = await api.createEvaluation(payload);
      toast.success(
        `Evaluation "${result.name}" (${result.run_id.substring(0, 10)}) completed successfully!`,
        'Evaluation Finished'
      );
      onNavigate('run-detail', result.run_id);
    } catch (err: any) {
      const msg = err.message || 'Evaluation execution failed';
      setExecutionError(msg);
      toast.error(msg, 'Execution Failed');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="new-eval-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Configure New Evaluation</h1>
          <p className="page-header-subtitle">
            Configure dataset benchmarks, select local or remote model providers, and trigger scoring.
          </p>
        </div>
      </div>

      <WizardHeader
        currentStep={currentStep}
        onStepClick={goToStep}
        maxStepReached={maxStepReached}
      />

      <div className="wizard-card" style={{ marginTop: 'var(--space-lg)' }}>
        {executionError && (
          <div className="toast-item error" role="alert">
            <AlertOctagon size={16} className="toast-icon" />
            <div className="toast-content">
              <div className="toast-title">Evaluation Run Failed</div>
              <div className="toast-message">{executionError}</div>
            </div>
          </div>
        )}

        {isExecuting ? (
          <div className="execution-progress-box">
            <div className="execution-spinner" />
            <div>
              <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>
                Executing Evaluation Run...
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)', marginTop: '4px' }}>
                Dispatching test cases concurrently to target model: <code>{target.model_identifier}</code>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Step 1: Dataset Selection */}
            {currentStep === 1 && (
              <div>
                <div className="wizard-card-title">
                  <span>Step 1: Evaluation Dataset</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Select a validated test case dataset from the project repository or provide raw inline JSONL.
                </p>
                <StepDataset
                  datasetPath={datasetPath}
                  datasetContent={datasetContent}
                  onSelectPath={setDatasetPath}
                  onSetContent={setDatasetContent}
                  onValidChange={setStep1Valid}
                />
              </div>
            )}

            {/* Step 2: Target Model & Provider */}
            {currentStep === 2 && (
              <div>
                <div className="wizard-card-title">
                  <span>Step 2: Target Model & Provider</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Specify the target LLM or reference system to benchmark. Supports verified local Ollama daemon.
                </p>
                <StepProvider
                  target={target}
                  onChange={setTarget}
                  onValidChange={setStep2Valid}
                />
              </div>
            )}

            {/* Step 3: Model Configuration Parameters */}
            {currentStep === 3 && (
              <div>
                <div className="wizard-card-title">
                  <span>Step 3: Sampling & Execution Parameters</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Tune model generation options and network connection limits.
                </p>
                <div className="grid-2">
                  <Input
                    label="Temperature"
                    type="number"
                    step="0.05"
                    min="0"
                    max="2"
                    isMonospace
                    value={target.temperature}
                    onChange={(e) => setTarget({ ...target, temperature: parseFloat(e.target.value) || 0 })}
                    hint="0.0 provides deterministic repeatable evaluation runs."
                  />
                  <Input
                    label="Timeout (seconds per prompt)"
                    type="number"
                    min="1"
                    max="300"
                    isMonospace
                    value={target.timeout_seconds}
                    onChange={(e) => setTarget({ ...target, timeout_seconds: parseFloat(e.target.value) || 60 })}
                  />
                  <Input
                    label="Max Response Tokens"
                    type="number"
                    isMonospace
                    placeholder="Unlimited"
                    value={target.max_tokens || ''}
                    onChange={(e) =>
                      setTarget({
                        ...target,
                        max_tokens: e.target.value ? parseInt(e.target.value, 10) : null,
                      })
                    }
                  />
                  <Input
                    label="Base URL"
                    isMonospace
                    value={target.base_url || ''}
                    onChange={(e) => setTarget({ ...target, base_url: e.target.value || null })}
                    placeholder="http://localhost:11434"
                  />
                </div>
              </div>
            )}

            {/* Step 4: Evaluators & Metrics */}
            {currentStep === 4 && (
              <div>
                <div className="wizard-card-title">
                  <span>Step 4: Evaluator Suite</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Choose deterministic string/schema validators or model-based LLM-as-judge evaluators.
                </p>
                <StepEvaluators
                  selectedEvaluators={evaluators}
                  onChange={setEvaluators}
                  onValidChange={setStep4Valid}
                />
              </div>
            )}

            {/* Step 5: Execution Controls */}
            {currentStep === 5 && (
              <div>
                <div className="wizard-card-title">
                  <span>Step 5: Execution Controls & Run Name</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Name the evaluation run and adjust concurrent async worker pool size.
                </p>
                <div className="grid-2">
                  <Input
                    label="Evaluation Run Name"
                    required
                    value={runName}
                    onChange={(e) => setRunName(e.target.value)}
                    placeholder="e.g. Qwen 2.5 3B Quality Benchmark"
                  />
                  <Input
                    label="Max Concurrency (workers)"
                    type="number"
                    min="1"
                    max="20"
                    isMonospace
                    value={concurrency}
                    onChange={(e) => setConcurrency(parseInt(e.target.value, 10) || 1)}
                    hint="Number of test cases evaluated in parallel."
                  />
                  <Input
                    label="Max Retries per Case"
                    type="number"
                    min="0"
                    max="5"
                    isMonospace
                    value={retries}
                    onChange={(e) => setRetries(parseInt(e.target.value, 10) || 0)}
                  />
                </div>
              </div>
            )}

            {/* Step 6: Review & Launch */}
            {currentStep === 6 && (
              <div>
                <div className="wizard-card-title">
                  <ShieldCheck size={18} color="var(--accent-primary)" />
                  <span>Step 6: Review Configuration</span>
                </div>
                <p className="wizard-card-subtitle" style={{ marginBottom: 'var(--space-md)' }}>
                  Verify configuration before initiating test execution against the local engine.
                </p>

                <div className="review-summary-card">
                  <div className="review-row">
                    <span className="review-label">Run Name</span>
                    <span className="review-value">{runName}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Dataset Source</span>
                    <span className="review-value">
                      {datasetPath || 'Custom Inline JSONL'}
                    </span>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Target Model</span>
                    <span className="review-value">
                      {target.model_identifier} ({target.provider_name})
                    </span>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Evaluators ({evaluators.length})</span>
                    <div className="flex-row gap-xs" style={{ flexWrap: 'wrap' }}>
                      {evaluators.map((e) => (
                        <Badge key={e.metric_id} variant="accent">
                          {e.evaluator_name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Concurrency & Retries</span>
                    <span className="review-value">
                      {concurrency} workers / {retries} retries max
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Wizard Navigation Footer */}
            <div className="wizard-footer-actions">
              <Button
                variant="outline"
                size="md"
                disabled={currentStep === 1}
                iconLeft={<ArrowLeft size={13} />}
                onClick={handlePrev}
              >
                Previous Step
              </Button>

              {currentStep < 6 ? (
                <Button
                  variant="primary"
                  size="md"
                  disabled={!canProceed()}
                  iconRight={<ArrowRight size={13} />}
                  onClick={handleNext}
                >
                  Continue
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="md"
                  iconLeft={<Play size={13} />}
                  onClick={handleLaunchEvaluation}
                  id="btn-launch-evaluation"
                >
                  Start Evaluation
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
