/**
 * Unit tests for Skeleton components
 */
import React from 'react';
import { render } from '@testing-library/react';
import { Skeleton, SkeletonCard, SkeletonMetricCard, SkeletonList } from '@/components/ui/Skeleton';

describe('Skeleton components', () => {
  describe('Skeleton', () => {
    it('renders with animate-pulse class', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild).toHaveClass('animate-pulse');
    });

    it('accepts additional className', () => {
      const { container } = render(<Skeleton className="w-32 h-4" />);
      expect(container.firstChild).toHaveClass('w-32', 'h-4');
    });
  });

  describe('SkeletonCard', () => {
    it('renders without crashing', () => {
      const { container } = render(<SkeletonCard />);
      expect(container.firstChild).toBeTruthy();
    });

    it('renders multiple skeleton lines', () => {
      const { container } = render(<SkeletonCard />);
      const pulseElements = container.querySelectorAll('.animate-pulse');
      expect(pulseElements.length).toBeGreaterThan(1);
    });
  });

  describe('SkeletonMetricCard', () => {
    it('renders without crashing', () => {
      const { container } = render(<SkeletonMetricCard />);
      expect(container.firstChild).toBeTruthy();
    });
  });

  describe('SkeletonList', () => {
    it('renders the specified number of rows', () => {
      const { container } = render(<SkeletonList rows={3} />);
      const pulseElements = container.querySelectorAll('.animate-pulse');
      expect(pulseElements.length).toBeGreaterThanOrEqual(3);
    });

    it('defaults to 4 rows when rows is not specified', () => {
      const { container } = render(<SkeletonList />);
      const pulseElements = container.querySelectorAll('.animate-pulse');
      expect(pulseElements.length).toBeGreaterThanOrEqual(4);
    });
  });
});
