import React from 'react';
import { ModelProfile, NavRoute } from '../../types';
import { HeroSection } from './HeroSection';
import { ModelDiscoveryPreview } from './ModelDiscoveryPreview';
import { WhyEvalForgeSection } from './WhyEvalForgeSection';
import { HowItWorksSection } from './HowItWorksSection';
import { ComparisonPreviewSection } from './ComparisonPreviewSection';
import { EvaluationPreviewSection } from './EvaluationPreviewSection';
import { LocalFirstSection } from './LocalFirstSection';
import { FinalCtaSection } from './FinalCtaSection';

interface LandingPageProps {
  onRouteChange: (route: NavRoute) => void;
  onSelectModel: (model: ModelProfile) => void;
  onAddToCompare: (modelId: string) => void;
  compareModelIds: string[];
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onRouteChange,
  onSelectModel,
  onAddToCompare,
  compareModelIds,
}) => {
  return (
    <div className="flex flex-col w-full">
      <HeroSection onRouteChange={onRouteChange} />
      <ModelDiscoveryPreview
        onRouteChange={onRouteChange}
        onSelectModel={onSelectModel}
        onAddToCompare={onAddToCompare}
        compareModelIds={compareModelIds}
      />
      <WhyEvalForgeSection />
      <HowItWorksSection />
      <ComparisonPreviewSection onRouteChange={onRouteChange} />
      <EvaluationPreviewSection onRouteChange={onRouteChange} />
      <LocalFirstSection />
      <FinalCtaSection onRouteChange={onRouteChange} />
    </div>
  );
};
