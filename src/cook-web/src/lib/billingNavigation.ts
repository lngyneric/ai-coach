export const BILLING_NAV_ITEMS: { label: string; href: string }[] = [];
export const BILLING_PACKAGES_HREF = '/admin/billing/packages';
export const BILLING_DETAILS_HREF = '/admin/billing/details';

export function isBillingEnabled() {
  return false;
}
