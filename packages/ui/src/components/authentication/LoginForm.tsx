"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, type SubmitHandler } from "react-hook-form";
import { z } from "zod";
import { GoogleColorIcon } from "../icons/GoogleColor";
import "./LoginForm.scss";
import { SVGProps } from "react";
import Link from "next/link";

const formSchema = z
  .object({
    email: z
      .string()
      .email({ message: "Must be a valid Email" })
      .min(1, "Email is required"),
    password: z.string().min(1, "Password is required"),
  })
  .required();
type FormValues = z.infer<typeof formSchema>;

interface LoginFormProps {
  authenticate: (
    prevstate: string,
    formData: FormValues
  ) => Promise<"Invalid credentials." | "Something went wrong." | undefined>;
  authenticateGoogle: () => Promise<
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
  } = useForm<FormValues>({ resolver: zodResolver(formSchema) });

  const onSubmit: SubmitHandler<FormValues> = async (data: FormValues) => {
    const res = await authenticate("", data);
    if (res) {
      setError("root.credentials", { message: res });
      resetField("password");
    } else {
      reset();
    }
  };

  async function handleGoogleClick(): Promise<void> {
    await authenticateGoogle();
  }

  return (
    <div className="login-form-main-container ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-3/5 ui-text-white">
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
              className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
                errors.email ? "ui-border-red-500 ui-border" : ""
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
              className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
                errors.password ? "ui-border-red-500 ui-border" : ""
              }`}
              id="password"
              type="password"
              {...register("password")}
            />
            <PasswordIcon />
          </div>
          <p className="ui-text-sm ui-text-red-500">
            {errors.password?.message}
          </p>
          <p className="ui-text-sm ui-text-red-500">
            {errors.root?.credentials?.message}
          </p>

          {/* Submit Buttons */}
          <div className="ui-flex ui-flex-row ui-gap-4 ui-w-full">
            <button
              className="sign-in-button ui-py-3 ui-px-10 ui-rounded-lg ui-flex-1"
              type="submit"
            >
              Sign In
            </button>
            <Link
              href="/signup"
              className="sign-up-button ui-py-3 ui-px-10 ui-rounded-lg ui-flex-1 ui-text-center"
            >
              Sign Up
            </Link>
          </div>
        </form>
      </div>
      <div className="separator">
        <div>or</div>
      </div>
      <button
        className="ui-flex ui-flex-row ui-items-center ui-justify-center ui-gap-3 ui-py-3 ui-px-10 ui-bg-[#161616] ui-w-full ui-rounded-lg"
        onClick={() => {
          handleGoogleClick().catch((e) => {
            // eslint-disable-next-line no-console -- Temporary until better logging
            console.log(e);
          });
        }}
        type="button"
      >
        <GoogleColorIcon />
        Sign In With Google
      </button>
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
