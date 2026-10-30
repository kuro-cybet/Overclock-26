import { describe, it, expect } from 'vitest';
import { tokens } from '../src/design-system/tokens';

describe('CampusOps Frontend Design System & Tokens', () => {
  it('should maintain the Creative Learning palette tokens', () => {
    expect(tokens.colors.ivory).toBe('#FFF4E9');
    expect(tokens.colors.peach).toBe('#FFD6BA');
    expect(tokens.colors.coral).toBe('#F29877');
    expect(tokens.colors.blue).toBe('#8EB9D8');
    expect(tokens.colors.deepBlue).toBe('#345873');
  });

  it('should have all 4 role accents configured', () => {
    expect(tokens.roleAccents.admin.color).toBe('#F29877');
    expect(tokens.roleAccents.technician.color).toBe('#287D70');
    expect(tokens.roleAccents.faculty.color).toBe('#8EB9D8');
    expect(tokens.roleAccents.student.color).toBe('#A58ACF');
  });

  it('should verify status badge color classes', () => {
    expect(tokens.statusColors.critical).toContain('bg-red-100');
    expect(tokens.statusColors.confirmed).toContain('bg-emerald-100');
  });
});

