import type { SubmitHandler } from "react-hook-form";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import Link from "next/link";
import * as yup from "yup";

const formSchema = yup
  .object({
    fullName: yup.string().required(),
    email: yup.string().email().required(),
    password: yup.string().required("Password is required"),
    passwordConfirmation: yup.string().oneOf([yup.ref("password")], "Passwords must match"),
  })
  .required();
type FormValues = yup.InferType<typeof formSchema>;

export function SignUpForm(): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: yupResolver(formSchema) });

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    // eslint-disable-next-line no-console -- Temporary
    console.log(JSON.stringify(data));
  };
  return (
    <div className="ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-3/5">
      <div className="ui-flex ui-flex-col ui-items-start ui-gap-5 ui-w-full">
        <form
          className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
          onSubmit={() => handleSubmit(onSubmit)}
        >
          {/* Full Name */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="fullName">
            Full Name
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="fullName"
            {...register("fullName")}
          />
          <p>{errors.fullName?.message}</p>
          {/* Email */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="email">
            Email
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="email"
            {...register("email")}
          />
          <p>{errors.email?.message}</p>
          {/* Password */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="password">
            Password
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="password"
            type="password"
            {...register("password")}
          />
          <p>{errors.password?.message}</p>
          {/* Confirm Password */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="passwordConfirmation">
            Confirm Password
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="passwordConfirmation"
            type="password"
            {...register("passwordConfirmation")}
          />
          <p>{errors.passwordConfirmation?.message}</p>
          {/* Submit */}
          <button className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg" type="submit">
            Next
          </button>
        </form>
        <span className="ui ui-font-medium ui-text-sm">
          By signing up, I agree to sessions,{" "}
          <Link className="ui ui-text-[#E75F33]" href="">
            Terms & Conditions
          </Link>
          {", "}
          <Link className="ui ui-text-[#E75F33]" href="">
            Privacy Policy
          </Link>
          , and to receive sessions news and updates.
        </span>
      </div>
    </div>
  );
}
