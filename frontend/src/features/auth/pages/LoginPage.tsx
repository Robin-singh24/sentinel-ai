import { Link, useNavigate } from "react-router-dom";
import { LoginForm } from "../components/LoginForm";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export function LoginPage() {
  const navigate = useNavigate();

  const handleSuccess = () => {
    navigate("/");
  };

  return (
    <div className="mx-auto w-full max-w-sm">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Login</CardTitle>
          <CardDescription>
            Enter your email below to login to your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={handleSuccess} />
        </CardContent>
        <CardFooter className="flex flex-col items-center">
          <p className="mt-4 text-sm text-center text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="underline hover:text-primary">
              Register
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
