import React from 'react';
interface Props { title: string }
export default function AdminTitle({ title }: Props) {
  return <h1 className="admin-title">{title}</h1>;
}
