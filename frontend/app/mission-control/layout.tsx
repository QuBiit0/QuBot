import DashboardLayout from '../dashboard/layout';

export default function MissionControlLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
