import React from 'react';
import {
  Play,
  Save,
  CheckCircle,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
} from 'lucide-react';
import { Button } from '../ui/Primitives';

interface TopToolbarProps {
  workflowName: string;
  onNameChange: (name: string) => void;
  onSave: () => void;
  onValidate: () => void;
  onEvaluate: () => void;
  isEvaluating: boolean;
  isValidating: boolean;
  validationStatus: { isValid: boolean; message?: string } | null;
}

export const TopToolbar: React.FC<TopToolbarProps> = ({
  workflowName,
  onNameChange,
  onSave,
  onValidate,
  onEvaluate,
  isEvaluating,
  isValidating,
  validationStatus,
}) => {
  return (
    <div className="h-12 bg-white border-b border-[#E2E8F0] px-4 flex items-center justify-between shrink-0 select-none z-10">
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={workflowName}
          onChange={(e) => onNameChange(e.target.value)}
          className="text-xs font-semibold text-[#111827] bg-transparent hover:bg-[#F8FAFC] focus:bg-white px-2 py-1 rounded border border-transparent hover:border-[#E2E8F0] focus:border-[#2563EB] focus:outline-none w-56 truncate"
          title="Click to edit workflow name"
        />

        {validationStatus && (
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${
              validationStatus.isValid
                ? 'bg-[#F0FDF4] text-[#16A34A] border-[#BBF7D0]'
                : 'bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]'
            }`}
          >
            {validationStatus.isValid ? (
              <>
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Ready to Evaluate</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" />
                <span className="truncate max-w-[200px]" title={validationStatus.message}>
                  {validationStatus.message || 'Validation Error'}
                </span>
              </>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onSave} icon={<Save className="w-3.5 h-3.5" />}>
          Save
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onValidate}
          disabled={isValidating}
          icon={<CheckCircle className="w-3.5 h-3.5" />}
        >
          {isValidating ? 'Validating...' : 'Validate'}
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onEvaluate}
          disabled={isEvaluating}
          icon={<Play className={`w-3.5 h-3.5 ${isEvaluating ? 'animate-pulse' : ''}`} />}
          className="bg-[#2563EB] hover:bg-[#1D4ED8] text-white shadow-sm"
        >
          {isEvaluating ? 'Evaluating...' : 'Evaluate'}
        </Button>
      </div>
    </div>
  );
};
