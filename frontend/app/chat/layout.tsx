import DashboardLayout from '../dashboard/layout';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
