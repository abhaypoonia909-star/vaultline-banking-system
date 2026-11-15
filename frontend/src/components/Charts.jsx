import { Bar, Doughnut } from "react-chartjs-2";
import { barOptions, doughnutOptions, palette } from "../services/charts";

export function FlowChart({ deposits, withdrawals }) {
  const data = {
    labels: ["Deposits", "Withdrawals"],
    datasets: [
      {
        data: [Number(deposits || 0), Number(withdrawals || 0)],
        backgroundColor: [palette.blue, palette.gold],
        borderWidth: 0,
      },
    ],
  };
  return (
    <div className="chart-box">
      <Doughnut data={data} options={doughnutOptions} />
    </div>
  );
}

export function LoginChart({ days }) {
  const rows = days || [];
  const data = {
    labels: rows.map((row) => row.date.slice(5)),
    datasets: [
      {
        label: "Failed",
        data: rows.map((row) => row.failed),
        backgroundColor: palette.danger,
        borderRadius: 6,
      },
      {
        label: "Successful",
        data: rows.map((row) => row.successful),
        backgroundColor: palette.ok,
        borderRadius: 6,
      },
    ],
  };
  return (
    <div className="chart-box">
      <Bar data={data} options={{ ...barOptions, plugins: { legend: { position: "bottom" } } }} />
    </div>
  );
}
