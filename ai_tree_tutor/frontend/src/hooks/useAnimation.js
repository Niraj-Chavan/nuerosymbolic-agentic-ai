import { useState, useCallback, useRef, useEffect } from 'react';
import useTreeStore from '../store/useTreeStore';

export function useAnimation() {
  const steps = useTreeStore((s) => s.animationSteps);
  const setHighlightedKeys = useTreeStore((s) => s.setHighlightedKeys);

  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1000);
  const intervalRef = useRef(null);

  const totalSteps = steps.length;

  const updateHighlight = useCallback(
    (step) => {
      const keys = steps[step]?.highlighted_nodes || [];
      setHighlightedKeys(keys);
    },
    [steps, setHighlightedKeys],
  );

  const play = useCallback(() => setIsPlaying(true), []);

  const pause = useCallback(() => setIsPlaying(false), []);

  const stepForward = useCallback(() => {
    setCurrentStep((prev) => {
      const next = Math.min(prev + 1, totalSteps - 1);
      updateHighlight(next);
      return next;
    });
  }, [totalSteps, updateHighlight]);

  const stepBackward = useCallback(() => {
    setCurrentStep((prev) => {
      const next = Math.max(prev - 1, 0);
      updateHighlight(next);
      return next;
    });
  }, [updateHighlight]);

  const goToStep = useCallback(
    (step) => {
      const clamped = Math.max(0, Math.min(step, totalSteps - 1));
      updateHighlight(clamped);
      setCurrentStep(clamped);
    },
    [totalSteps, updateHighlight],
  );

  const changeSpeed = useCallback((newSpeed) => setSpeed(newSpeed), []);

  useEffect(() => {
    if (isPlaying && totalSteps > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= totalSteps - 1) {
            setIsPlaying(false);
            return prev;
          }
          const next = prev + 1;
          updateHighlight(next);
          return next;
        });
      }, speed);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, speed, totalSteps, updateHighlight]);

  useEffect(() => {
    setCurrentStep(0);
    setIsPlaying(false);
    setHighlightedKeys(steps[0]?.highlighted_nodes || []);
  }, [steps, setHighlightedKeys]);

  const getTreeSnapshot = useCallback(() => {
    return steps[currentStep]?.tree || null;
  }, [steps, currentStep]);

  return {
    steps,
    currentStep,
    currentStepData: steps[currentStep] || null,
    totalSteps,
    isPlaying,
    speed,
    play,
    pause,
    stepForward,
    stepBackward,
    goToStep,
    changeSpeed,
    getTreeSnapshot,
    isActive: steps.length > 0,
  };
}
