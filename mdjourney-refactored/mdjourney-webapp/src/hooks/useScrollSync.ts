import { useEffect, useRef, useCallback } from 'react';

interface UseScrollSyncOptions {
  sections: Array<{ id: string }>;
  activeSection: string;
  onActiveSectionChange: (sectionId: string) => void;
  threshold?: number;
  rootMargin?: string;
}

/**
 * Custom hook for synchronizing scroll position with active section
 * Uses Intersection Observer to detect which section is currently visible
 */
export const useScrollSync = ({
  sections,
  activeSection,
  onActiveSectionChange,
  threshold = 0.3, // 30% of section must be visible
  rootMargin = '-20% 0px -20% 0px' // Reduce trigger area for better accuracy
}: UseScrollSyncOptions) => {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sectionsInViewRef = useRef<Set<string>>(new Set());
  const isManualScrollRef = useRef(false);

  // Callback for intersection observer
  const handleIntersection = useCallback((entries: IntersectionObserverEntry[]) => {
    // Don't update if this is a manual scroll (user clicked navigation)
    if (isManualScrollRef.current) {
      return;
    }

    entries.forEach((entry) => {
      const sectionId = entry.target.getAttribute('data-section-id');
      if (!sectionId) return;

      if (entry.isIntersecting) {
        sectionsInViewRef.current.add(sectionId);
      } else {
        sectionsInViewRef.current.delete(sectionId);
      }
    });

    // Find the most appropriate section to highlight
    const visibleSections = Array.from(sectionsInViewRef.current);
    if (visibleSections.length > 0) {
      // If multiple sections are visible, choose based on scroll direction
      // For now, choose the first visible section in document order
      const orderedVisibleSections = sections
        .map(s => s.id)
        .filter(id => visibleSections.includes(id));

      if (orderedVisibleSections.length > 0 && orderedVisibleSections[0] !== activeSection) {
        onActiveSectionChange(orderedVisibleSections[0]);
      }
    }
  }, [sections, activeSection, onActiveSectionChange]);

  // Set up intersection observer
  useEffect(() => {
    // Clean up previous observer
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    // Create new observer
    observerRef.current = new IntersectionObserver(handleIntersection, {
      threshold,
      rootMargin,
    });

    // Observe all section elements
    sections.forEach(({ id }) => {
      const element = document.querySelector(`[data-section-id="${id}"]`);
      if (element && observerRef.current) {
        observerRef.current.observe(element);
      }
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [sections, handleIntersection, threshold, rootMargin]);

  // Manual scroll function (for navigation clicks)
  const scrollToSection = useCallback((sectionId: string, behavior: 'smooth' | 'auto' = 'smooth') => {
    // Set flag to prevent observer from interfering
    isManualScrollRef.current = true;

    // Update active section immediately
    onActiveSectionChange(sectionId);

    // Scroll to section
    const element = document.querySelector(`#section-${sectionId}`);
    if (element) {
      element.scrollIntoView({
        behavior,
        block: 'start',
      });
    }

    // Clear flag after scroll completes
    setTimeout(() => {
      isManualScrollRef.current = false;
    }, behavior === 'smooth' ? 800 : 100);
  }, [onActiveSectionChange]);

  // Scroll to field function
  const scrollToField = useCallback((fieldId: string, sectionId?: string) => {
    // Set flag to prevent observer from interfering
    isManualScrollRef.current = true;

    // Update active section if provided
    if (sectionId) {
      onActiveSectionChange(sectionId);
    }

    // Scroll to field
    const element = document.querySelector(`[data-field-id="${fieldId}"]`);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });

      // Focus the field if it's an input
      const input = element.querySelector('input, textarea, select') as HTMLElement;
      if (input && typeof input.focus === 'function') {
        setTimeout(() => input.focus(), 300);
      }
    }

    // Clear flag after scroll completes
    setTimeout(() => {
      isManualScrollRef.current = false;
    }, 800);
  }, [onActiveSectionChange]);

  return {
    scrollToSection,
    scrollToField,
  };
};