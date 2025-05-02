"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, type SubmitHandler } from "react-hook-form";
import { z } from "zod";
import { GoogleColorIcon } from "../icons/GoogleColor";
import "./LoginForm.scss";
import { SVGProps, useEffect } from "react";
import Link from "next/link";
import { CommonCheckbox } from "../common/CommonCheckbox";

const formSchema = z
  .object({
    email: z
      .string()
      .email({ message: "Must be a valid Email" })
      .min(1, "Email is required"),
    password: z.string().min(1, "Password is required"),
    rememberMe: z.boolean().optional().default(false),
  })
  .required();
type FormValues = z.infer<typeof formSchema>;

interface LoginFormProps {
  authenticate: (
    prevstate: string,
    formData: FormValues
  ) => Promise<"Invalid credentials." | "Something went wrong." | undefined>;
  authenticateGoogle?: () => Promise<
    "Invalid credentials." | "Something went wrong." | undefined
  >;
}

export function LogInForm({
  authenticate,
  authenticateGoogle,
}: LoginFormProps): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
    resetField,
    setValue,
    getValues,
  } = useForm<FormValues>({ resolver: zodResolver(formSchema) });

  const onSubmit: SubmitHandler<FormValues> = async (data: FormValues) => {
    // Handle remember me functionality
    if (data.rememberMe) {
      // Store email in localStorage
      localStorage.setItem("rememberedEmail", data.email);
      localStorage.setItem("rememberMe", "true");
    } else {
      // Clear remembered email
      localStorage.removeItem("rememberedEmail");
      localStorage.removeItem("rememberMe");
    }

    const res = await authenticate("", data);
    if (res) {
      setError("root.credentials", { message: res });
      resetField("password");
    } else {
      // If login is successful and remember me is not checked, clear the storage
      if (!data.rememberMe) {
        localStorage.removeItem("rememberedEmail");
        localStorage.removeItem("rememberMe");
      }
      reset();
    }
  };

  async function handleGoogleClick(): Promise<void> {
    if (!authenticateGoogle) {
      return;
    }
    await authenticateGoogle();
  }

  // Initialize form with remembered values
  useEffect(() => {
    // Check if we're in a browser environment
    if (typeof window !== "undefined") {
      const rememberedEmail = localStorage.getItem("rememberedEmail");
      const rememberMe = localStorage.getItem("rememberMe") === "true";

      if (rememberedEmail && rememberMe) {
        setValue("email", rememberedEmail);
        setValue("rememberMe", true);
      }
    }
  }, [setValue]);

  return (
    <div className="login-form-main-container ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-full ui-max-w-l ui-text-white">
      <div className="ui-flex ui-flex-col ui-items-start ui-gap-5 ui-w-full">
        <form
          id="login-form"
          className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
          // eslint-disable-next-line @typescript-eslint/no-misused-promises -- It's meant to be like this
          onSubmit={handleSubmit(onSubmit)}
        >
          {/* Email */}
          <label
            className="labels ui-font-semibold ui-font-source_sans"
            htmlFor="email"
          >
            Email
          </label>
          <div className="input-wrapper">
            <input
              className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${errors.email ? "ui-border-red-500 ui-border" : ""
                }`}
              id="email"
              {...register("email")}
            />
            <EmailIcon />
          </div>
          <p className="ui-text-sm ui-text-red-500">{errors.email?.message}</p>

          {/* Password */}
          <label
            className="labels ui-font-semibold ui-font-source_sans"
            htmlFor="password"
          >
            Password
          </label>
          <div className="input-wrapper">
            <input
              className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${errors.password ? "ui-border-red-500 ui-border" : ""
                }`}
              id="password"
              type="password"
              {...register("password")}
            />
            <PasswordIcon />
          </div>
          {/* Remember Me and Forgot Password */}
          <div className="auth-options-container">
            <div className="remember-me-container">
              <CommonCheckbox
                label="Remember me"
                defaultTrue={
                  typeof window !== "undefined" &&
                  localStorage.getItem("rememberMe") === "true"
                }
                onChange={(checked) => {
                  setValue("rememberMe", checked);
                  // Update localStorage immediately when checkbox changes
                  if (typeof window !== "undefined") {
                    if (checked) {
                      const email = getValues("email");
                      if (email) {
                        localStorage.setItem("rememberedEmail", email);
                        localStorage.setItem("rememberMe", "true");
                      }
                    } else {
                      localStorage.removeItem("rememberedEmail");
                      localStorage.removeItem("rememberMe");
                    }
                  }
                }}
              />
            </div>
            <Link
              href="/forgot-password"
              className="forgot-password-link ui-text-sm ui-text-gray-400 hover:ui-text-gray-300"
            >
              Forgot password?
            </Link>
          </div>
          <p className="ui-text-sm ui-text-red-500">
            {errors.password?.message}
          </p>
          <p className="ui-text-sm ui-text-red-500">
            {errors.root?.credentials?.message}
          </p>

          {/* Submit Button */}
          <div className="ui-w-full ui-mt-2">
            <button
              className="sign-in-button ui-py-3 ui-px-10 ui-rounded-lg ui-w-full"
              type="submit"
            >
              Sign In
            </button>
          </div>
        </form>
      </div>
      {authenticateGoogle !== undefined ? (<>
        <div className="separator">
          <div>or</div>
        </div><button
          className="ui-flex ui-flex-row ui-items-center ui-justify-center ui-gap-3 ui-py-3 ui-px-10 ui-bg-[#161616] ui-w-full ui-rounded-lg"
          onClick={() => {
            handleGoogleClick().catch((e: unknown) => {
              // eslint-disable-next-line no-console -- Temporary until better logging
              console.log(e);
            });
          }}
          type="button"
        >
          <GoogleColorIcon />
          Sign In With Google
        </button></>
      ) : null}
      {/* Register Link */}
      <div className="ui-flex ui-justify-center ui-w-full ui-mt-6">
        <span className="ui-text-sm ui-text-gray-400">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="register-link ui-text-[#E75F33]">
            Register
          </Link>
        </span>
      </div>
    </div>
  );
}

function PasswordIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={18}
      height={22}
      fill="none"
      {...props}
    >
      <path
        fill="#898989"
        d="M15 7.5h2a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1v-12a1 1 0 0 1 1-1h2v-1a6 6 0 1 1 12 0v1Zm-2 0v-1a4 4 0 1 0-8 0v1h8Zm-5 6v2h2v-2H8Zm-4 0v2h2v-2H4Zm8 0v2h2v-2h-2Z"
      />
    </svg>
  );
}

function EmailIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={20}
      height={17}
      fill="none"
      {...props}
    >
      <path
        fill="#898989"
        d="M18 .5H2C.9.5.01 1.4.01 2.5L0 14.5c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-12c0-1.1-.9-2-2-2Zm0 4-8 5-8-5v-2l8 5 8-5v2Z"
      />
    </svg>
  );
}
