import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);
ChartJS.defaults.color = "#9aafc6";
ChartJS.defaults.borderColor = "rgba(158, 184, 214, 0.14)";
ChartJS.defaults.font.family = '"Outfit", "Segoe UI", sans-serif';

export const palette = {
  blue: "#7eacff",
  gold: "#d7b483",
  danger: "#f08a86",
  ok: "#49d6a3",
};

export const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
  cutout: "68%",
};

export const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, ticks: { precision: 0 } },
  },
};
