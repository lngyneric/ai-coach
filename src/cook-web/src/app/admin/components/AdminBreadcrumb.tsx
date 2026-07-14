import React from 'react';
interface Props { items: { label: string }[] }
export default function AdminBreadcrumb({ items }: Props) {
  return <nav className="admin-breadcrumb">{items.map((i, idx) => <span key={idx}>{i.label}{idx < items.length-1 ? ' / ' : ''}</span>)}</nav>;
}
