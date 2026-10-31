/**
 * Centralized Indian Rupee (INR) currency formatter for CampusOps.
 * Formats numeric monetary amounts using standard Indian digit grouping (e.g. ₹1,500, ₹1,25,000, ₹10,00,000).
 */
export const formatINR = (amount: number | string | null | undefined): string => {
  const num = typeof amount === 'string' ? parseFloat(amount) : Number(amount || 0);
  if (isNaN(num)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(num);
};

