import {
  createRootRoute,
  createRoute,
  Outlet,
  Navigate,
} from "@tanstack/react-router";
import { lazy } from "react";

const LoginPage = lazy(() => import("./login"));
const DesktopPage = lazy(() => import("./desktop"));
const ClinicalPage = lazy(() => import("./clinical"));

const rootRoute = createRootRoute({
  component: () => (
    <div className="h-screen w-screen overflow-hidden">
      <Outlet />
    </div>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Navigate to="/login" />,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

const desktopRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/desktop",
  component: DesktopPage,
});

const clinicalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/clinical/$moduleId",
  component: ClinicalPage,
});

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  desktopRoute,
  clinicalRoute,
]);
