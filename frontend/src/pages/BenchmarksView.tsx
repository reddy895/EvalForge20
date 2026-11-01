import React, { useEffect, useState } from 'react';
import { BookmarkCheck, RefreshCw, Shield, Code, Calculator, Brain, FileCheck } from 'lucide-react';
import { Badge, EmptyState } from '../components/ui/Primitives';

export const BenchmarksView: React.FC = () => {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchBenchmarks = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/benchmarks');
      if (res.ok) {
        const data = await res.json();
        setBenchmarks(data.benchmarks || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, []);

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'mathematics':
        return <Calculator className="w-4 h-4 text-[#2563EB]" />;
      case 'coding':
        return <Code className="w-4 h-4 text-[#16A34A]" />;
      case 'reasoning':
        return <Brain className="w-4 h-4 text-[#7C3AED]" />;
      case 'safety':
        return <Shield className="w-4 h-4 text-[#DC2626]" />;
      case 'structured output':
        return <FileCheck className="w-4 h-4 text-[#D97706]" />;
      default:
        return <BookmarkCheck className="w-4 h-4 text-[#2563EB]" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Standard Benchmark Suites</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Curated evaluation suites with documented licenses, ground truth schemas, and scoring criteria
          </p>
        </div>
        <button
          onClick={fetchBenchmarks}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E2E8F0] bg-white text-xs font-medium text-[#64748B] hover:text-[#111827] shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-[#64748B] text-xs">
          <RefreshCw className="w-5 h-5 animate-spin mr-2 text-[#2563EB]" />
          Loading benchmarks...
        </div>
      ) : benchmarks.length === 0 ? (
        <EmptyState
          icon={BookmarkCheck}
          title="No Benchmark Suites Found"
          description="Check that the benchmark registry is initialized in the backend."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {benchmarks.map((suite) => (
            <div
              key={suite.id}
              className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-3 hover:border-[#CBD5E1] transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-md bg-[#F8FAFC] border border-[#E2E8F0]">
                      {getCategoryIcon(suite.category)}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827]">{suite.name}</div>
                      <div className="text-[10px] text-[#64748B] font-mono">{suite.category}</div>
                    </div>
                  </div>
                  <Badge variant="primary">{suite.sample_count || 5} cases</Badge>
                </div>

                <p className="text-xs text-[#64748B] leading-relaxed">
                  {suite.description || 'Standard evaluation suite for local LLM verification.'}
                </p>

                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2.5 space-y-1.5 text-[11px]">
                  <div className="flex justify-between text-[#64748B]">
                    <span>Metric Evaluator:</span>
                    <span className="font-semibold text-[#111827]">{suite.default_evaluator || 'exact_match'}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>License:</span>
                    <span className="font-mono text-[#111827]">{suite.license || 'MIT'}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>Ground Truth:</span>
                    <span className="text-[#16A34A] font-semibold">Strict Reference Answers</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#E2E8F0] text-[10px] text-[#94A3B8] font-mono">
                Identifier: {suite.id}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
