"use client";
import type { JSX } from "react";
import type { SubmitHandler } from "react-hook-form";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import "./SignUpForm.scss";

const formSchema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    email: z
      .string()
      .email({ message: "Must be a valid Email" })
      .min(1, "Email is required"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    passwordConfirmation: z
      .string()
      .min(1, "Password confirmation is required"),
  })
  .required()
  .refine((data) => data.password === data.passwordConfirmation, {
    path: ["passwordConfirmation"],
    message: "Password don't match",
  });
type FormValues = z.infer<typeof formSchema>;

export function SignUpForm(): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: "onSubmit",
    reValidateMode: "onChange",
  });

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    // eslint-disable-next-line no-console -- Temporary
    console.log(JSON.stringify(data));
    reset();
  };

  return (
    <div className="ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-full ui-max-w-xl">
      <div className="ui-flex ui-flex-col ui-items-start ui-gap-5 ui-w-full">
        <form
          id="signup-form"
          className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
          // eslint-disable-next-line @typescript-eslint/no-misused-promises -- This is meant to be like this.
          onSubmit={handleSubmit(onSubmit)}
        >
          {/* Name Fields */}
          <div className="ui-w-full">
            <div className="ui-flex ui-flex-row ui-gap-4 ui-w-full">
              {/* First Name */}
              <div className="ui-flex ui-flex-col ui-w-1/2 ui-gap-3">
                <label
                  className="ui-text-lg ui-font-semibold ui-font-source_sans"
                  htmlFor="firstName"
                >
                  First Name
                </label>
                <input
                  className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
                    errors.firstName ? "ui-border-red-500 ui-border" : ""
                  }`}
                  id="firstName"
                  {...register("firstName")}
                />
                <p className="ui-text-sm ui-text-red-500">
                  {errors.firstName?.message}
                </p>
              </div>

              {/* Last Name */}
              <div className="ui-flex ui-flex-col ui-w-1/2 ui-gap-3">
                <label
                  className="ui-text-lg ui-font-semibold ui-font-source_sans"
                  htmlFor="lastName"
                >
                  Last Name
                </label>
                <input
                  className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
                    errors.lastName ? "ui-border-red-500 ui-border" : ""
                  }`}
                  id="lastName"
                  {...register("lastName")}
                />
                <p className="ui-text-sm ui-text-red-500">
                  {errors.lastName?.message}
                </p>
              </div>
            </div>
          </div>
          {/* Email */}
          <label
            className="ui-text-lg ui-font-semibold ui-font-source_sans"
            htmlFor="email"
          >
            Email
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.email ? "ui-border-red-500 ui-border" : ""
            }`}
            id="email"
            {...register("email")}
          />
          <p className="ui-text-sm ui-text-red-500">{errors.email?.message}</p>
          {/* Password */}
          <label
            className="ui-text-lg ui-font-semibold ui-font-source_sans"
            htmlFor="password"
          >
            Password
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.password ? "ui-border-red-500 ui-border" : ""
            }`}
            id="password"
            type="password"
            {...register("password")}
          />
          <p className="ui-text-sm ui-text-red-500">
            {errors.password?.message}
          </p>
          {/* Confirm Password */}
          <label
            className="ui-text-lg ui-font-semibold ui-font-source_sans"
            htmlFor="passwordConfirmation"
          >
            Confirm Password
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.passwordConfirmation ? "ui-border-red-500 ui-border" : ""
            }`}
            id="passwordConfirmation"
            type="password"
            {...register("passwordConfirmation")}
          />
          <p className="ui-text-sm ui-text-red-500">
            {errors.passwordConfirmation?.message}
          </p>
          {/* Submit */}
          <button
            className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg ui-w-full ui-font-medium"
            type="submit"
          >
            Sign Up
          </button>
        </form>
      </div>
      {/* Sign In Link */}
      <div className="ui-flex ui-justify-center ui-w-full ui-mt-4">
        <span className="ui-text-sm ui-text-gray-400">
          Already have an account?{" "}
          <Link href="/login" className="sign-in-link">
            Sign in
          </Link>
        </span>
      </div>
    </div>
  );
}
