import DashboardLayout from '../dashboard/layout';

export default function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
