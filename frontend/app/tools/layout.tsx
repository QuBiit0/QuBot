import DashboardLayout from '../dashboard/layout';

export default function ToolsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
