import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";

export default function PublicLayout() {
  const location = useLocation();

  const isHomePage = location.pathname === "/";

  return (
    <>
      <Navbar />

      <main>
        <Outlet />
      </main>

      {isHomePage && <Footer />}
    </>
  );
}
