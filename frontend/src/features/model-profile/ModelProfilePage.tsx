import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  HardDrive,
  Cloud,
  Cpu,
  Layers,
  Sparkles,
  Scale,
  PlayCircle,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../../services/api';
import type { ModelProfile } from '../../types';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

interface ModelProfilePageProps {
  modelId: string;
  onBack: () => void;
  onCompare: (modelId: string) => void;
  onEvaluate: (modelTag: string) => void;
}

export const ModelProfilePage: React.FC<ModelProfilePageProps> = ({
  modelId,
  onBack,
  onCompare,
  onEvaluate,
}) => {
  const [profile, setProfile] = useState<ModelProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await api.getModelProfile(modelId);
        setProfile(res);
      } catch (e: any) {
        setError(e.message || 'Failed to load model profile');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, [modelId]);

  if (isLoading) {
    return (
      <div className="page-container loading-state">
        <span className="spinner" />
        <p>Loading technical profile for {modelId}...</p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="page-container">
        <Button variant="outline" size="sm" onClick={onBack} iconLeft={<ArrowLeft size={14} />}>
          Back to Catalog
        </Button>
        <div className="error-banner" style={{ marginTop: '16px' }}>
          {error || 'Model profile not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="page-container model-profile-page">
      {/* Top Header & Navigation */}
      <div className="profile-header-bar">
        <Button variant="outline" size="sm" onClick={onBack} iconLeft={<ArrowLeft size={14} />}>
          Back to Catalog
        </Button>

        <div className="flex-row gap-xs">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCompare(profile.id)}
            iconLeft={<Scale size={14} />}
          >
            Add to Compare
          </Button>

          {profile.is_local && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onEvaluate(profile.model_identifier)}
              iconLeft={<PlayCircle size={14} />}
            >
              Run Evaluation
            </Button>
          )}
        </div>
      </div>

      {/* Main Model Headline Card */}
      <div className="profile-hero-card">
        <div className="hero-top-row">
          <div>
            <span className="profile-provider">{profile.provider}</span>
            <h1 className="profile-title">{profile.name}</h1>
            <span className="profile-identifier font-mono">{profile.model_identifier}</span>
          </div>

          <div>
            {profile.is_installed ? (
              <Badge variant="success">
                <CheckCircle2 size={12} style={{ marginRight: '4px' }} />
                Installed in Local Ollama
              </Badge>
            ) : profile.is_local ? (
              <Badge variant="neutral">
                <HardDrive size={12} style={{ marginRight: '4px' }} />
                Ollama Compatible
              </Badge>
            ) : (
              <Badge variant="info">
                <Cloud size={12} style={{ marginRight: '4px' }} />
                Frontier Cloud API
              </Badge>
            )}
          </div>
        </div>

        <p className="profile-description">{profile.description}</p>

        {/* Technical Highlights Bar */}
        <div className="profile-specs-grid">
          <div className="spec-box">
            <span className="spec-label">Parameters</span>
            <span className="spec-val font-mono">{profile.parameter_count || 'Dense'}</span>
          </div>
          <div className="spec-box">
            <span className="spec-label">Context Window</span>
            <span className="spec-val font-mono">{profile.context_window.toLocaleString()} tokens</span>
          </div>
          <div className="spec-box">
            <span className="spec-label">Architecture</span>
            <span className="spec-val">{profile.architecture || profile.family}</span>
          </div>
          <div className="spec-box">
            <span className="spec-label">License</span>
            <span className="spec-val">{profile.license}</span>
          </div>
          <div className="spec-box">
            <span className="spec-label">Min System RAM</span>
            <span className="spec-val font-mono">
              {profile.hardware.min_ram_gb > 0 ? `${profile.hardware.min_ram_gb} GB` : 'None (API)'}
            </span>
          </div>
          <div className="spec-box">
            <span className="spec-label">Token Pricing</span>
            <span className="spec-val font-mono">
              {profile.is_local ? 'Free ($0.00)' : `$${profile.pricing?.input_cost_per_m} / $${profile.pricing?.output_cost_per_m}`}
            </span>
          </div>
        </div>
      </div>

      {/* Sections Grid */}
      <div className="profile-sections-grid">
        {/* Left Column: Benchmarks & Capabilities */}
        <div className="profile-left-col">
          {/* Verified Benchmarks Section */}
          <div className="profile-panel">
            <div className="panel-header">
              <Sparkles size={16} className="accent-icon" />
              <h3>Verified Benchmark Results</h3>
            </div>

            {profile.benchmarks.length === 0 ? (
              <p className="empty-panel-text">No standardized benchmark records logged yet.</p>
            ) : (
              <table className="profile-table">
                <thead>
                  <tr>
                    <th>Benchmark</th>
                    <th>Metric</th>
                    <th>Score</th>
                    <th>Evidence Source</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.benchmarks.map((b, i) => (
                    <tr key={i}>
                      <td className="font-bold">{b.benchmark_name}</td>
                      <td>{b.metric}</td>
                      <td className="font-mono score-cell font-bold">{b.score}%</td>
                      <td className="source-cell">{b.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Capabilities & Modalities */}
          <div className="profile-panel">
            <div className="panel-header">
              <Layers size={16} className="accent-icon" />
              <h3>Supported Capabilities & Interfaces</h3>
            </div>

            <div className="capabilities-grid">
              <div className="cap-card">
                <span className="cap-title">Structured JSON Output</span>
                <span className={`cap-status ${profile.supports_structured_output ? 'yes' : 'no'}`}>
                  {profile.supports_structured_output ? '✓ Verified Support' : '✗ Not Verified'}
                </span>
                <p className="cap-desc">Direct schema adherence without syntax drift.</p>
              </div>

              <div className="cap-card">
                <span className="cap-title">Tool Use / Function Calling</span>
                <span className={`cap-status ${profile.supports_tools ? 'yes' : 'no'}`}>
                  {profile.supports_tools ? '✓ Verified Support' : '✗ Not Verified'}
                </span>
                <p className="cap-desc">Autonomous action planning & parameter extraction.</p>
              </div>

              <div className="cap-card">
                <span className="cap-title">Input/Output Modalities</span>
                <span className="cap-val font-mono">{profile.modalities.join(', ')}</span>
                <p className="cap-desc">Supported multi-modal data streams.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Hardware & Strengths/Weaknesses */}
        <div className="profile-right-col">
          {/* Hardware Feasibility */}
          <div className="profile-panel">
            <div className="panel-header">
              <Cpu size={16} className="accent-icon" />
              <h3>Hardware Feasibility</h3>
            </div>

            <div className="hardware-specs-list">
              <div className="hw-row">
                <span>Minimum System RAM:</span>
                <strong className="font-mono">{profile.hardware.min_ram_gb} GB</strong>
              </div>
              <div className="hw-row">
                <span>Recommended RAM:</span>
                <strong className="font-mono">{profile.hardware.recommended_ram_gb} GB</strong>
              </div>
              <div className="hw-row">
                <span>Minimum GPU VRAM:</span>
                <strong className="font-mono">
                  {profile.hardware.min_vram_gb ? `${profile.hardware.min_vram_gb} GB` : 'CPU Only Supported'}
                </strong>
              </div>
              <div className="hw-row">
                <span>Quantization Format:</span>
                <span className="font-mono">{profile.hardware.quantization}</span>
              </div>
              <div className="hw-row">
                <span>Disk Space:</span>
                <span className="font-mono">{profile.hardware.disk_space_gb} GB</span>
              </div>
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="profile-panel">
            <div className="panel-header">
              <CheckCircle2 size={16} className="accent-icon" />
              <h3>Strengths & Recommended Tasks</h3>
            </div>

            <ul className="profile-bullets strengths">
              {profile.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>

            <div className="tasks-tags-container">
              {profile.recommended_tasks.map((task) => (
                <span key={task} className="tag-pill task">
                  {task.replace('_', ' ')}
                </span>
              ))}
            </div>

            {profile.weaknesses.length > 0 && (
              <>
                <div className="panel-header" style={{ marginTop: '16px' }}>
                  <AlertTriangle size={16} style={{ color: 'var(--status-warning)' }} />
                  <h3>Known Limitations & Unsuitable Tasks</h3>
                </div>

                <ul className="profile-bullets weaknesses">
                  {profile.weaknesses.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
