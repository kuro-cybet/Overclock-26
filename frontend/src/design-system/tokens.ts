export const tokens = {
  colors: {
    ivory: "#FFF4E9",       // Page backgrounds and warm surfaces
    peach: "#FFD6BA",       // Selected navigation, soft emphasis and panels
    coral: "#F29877",       // Admin accent and secondary actions
    blue: "#8EB9D8",        // Faculty accent and informational elements
    deepBlue: "#345873",    // Sidebar, primary buttons and headings
  },
  roleAccents: {
    admin: {
      name: "Admin",
      color: "#F29877",
      bgLight: "rgba(242, 152, 119, 0.15)",
      border: "rgba(242, 152, 119, 0.4)",
      badgeClass: "bg-[#F29877]/20 text-[#c25833] border-[#F29877]/40",
    },
    technician: {
      name: "Technicians",
      color: "#287D70",
      bgLight: "rgba(40, 125, 112, 0.15)",
      border: "rgba(40, 125, 112, 0.4)",
      badgeClass: "bg-[#287D70]/20 text-[#1b584e] border-[#287D70]/40",
    },
    faculty: {
      name: "Faculty",
      color: "#8EB9D8",
      bgLight: "rgba(142, 185, 216, 0.2)",
      border: "rgba(142, 185, 216, 0.5)",
      badgeClass: "bg-[#8EB9D8]/30 text-[#1f4a6e] border-[#8EB9D8]/50",
    },
    student: {
      name: "Students",
      color: "#A58ACF",
      bgLight: "rgba(165, 138, 207, 0.2)",
      border: "rgba(165, 138, 207, 0.5)",
      badgeClass: "bg-[#A58ACF]/25 text-[#543b7a] border-[#A58ACF]/50",
    }
  },
  statusColors: {
    critical: "bg-red-100 text-red-800 border-red-300",
    high: "bg-orange-100 text-orange-800 border-orange-300",
    medium: "bg-amber-100 text-amber-800 border-amber-300",
    low: "bg-emerald-100 text-emerald-800 border-emerald-300",
    confirmed: "bg-emerald-100 text-emerald-800 border-emerald-300",
    stale: "bg-amber-100 text-amber-800 border-amber-300",
    unconfirmed: "bg-rose-100 text-rose-800 border-rose-300",
    open: "bg-blue-100 text-blue-800 border-blue-300",
    in_progress: "bg-indigo-100 text-indigo-800 border-indigo-300",
    blocked: "bg-red-100 text-red-800 border-red-300",
    completed: "bg-emerald-100 text-emerald-800 border-emerald-300",
    resolved: "bg-teal-100 text-teal-800 border-teal-300"
  }
};

