import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Map;

/** Exercises the registered sharing argument converter in the actual R8 output. */
public class SharingReleaseProbe {
  public static void main(String[] names) throws Exception {
    try {
      check(names);
    } catch (Throwable error) {
      error.printStackTrace();
      System.exit(1);
    }
  }

  private static void check(String[] names) throws Exception {
    Object module = Class.forName(names[0]).getConstructor().newInstance();
    Object definition = module.getClass().getMethod(names[1]).invoke(module);
    Object share = null;
    for (Field field : definition.getClass().getDeclaredFields()) {
      field.setAccessible(true);
      Object value = field.get(definition);
      if (value instanceof Map && ((Map<?, ?>) value).containsKey("shareAsync")) {
        share = ((Map<?, ?>) value).get("shareAsync");
        break;
      }
    }
    if (share == null) throw new AssertionError("No registered shareAsync function");
    Field arguments = Class.forName(names[2]).getDeclaredField(names[3]);
    arguments.setAccessible(true);
    Object optionsType = ((Object[]) arguments.get(share))[1];
    Field kTypeField = Class.forName(names[4]).getDeclaredField(names[5]);
    kTypeField.setAccessible(true);
    Object kType = kTypeField.get(optionsType);
    Class<?> providerClass = Class.forName(names[6]);
    Field instance = providerClass.getDeclaredField(names[7]);
    instance.setAccessible(true);
    Object provider = instance.get(null);
    Method obtain = null;
    for (Method method : providerClass.getMethods()) {
      if (method.getName().equals(names[8]) && method.getParameterCount() == 1) {
        obtain = method;
        break;
      }
    }
    if (obtain == null) throw new AssertionError("No argument converter provider");
    Object converter = obtain.invoke(provider, kType);
    Method convert = Class.forName(names[9]).getMethod(
        names[10], Object.class, Class.forName(names[11]), boolean.class);
    Class<?> mapClass = Class.forName("com.facebook.react.bridge.JavaOnlyMap");
    Method put = mapClass.getMethod("putString", String.class, String.class);
    Method get = mapClass.getMethod("getString", String.class);
    for (String title : new String[] { "Share", "Instagram", "Facebook", "YouTube", "साझा करें", null }) {
      Object map = mapClass.getConstructor().newInstance();
      put.invoke(map, "mimeType", "video/mp4");
      put.invoke(map, "UTI", "public.mpeg-4");
      if (title != null) put.invoke(map, "dialogTitle", title);
      // The old release crashes here while reflecting SharingOptions @Field.
      Object result = convert.invoke(converter, map, null, false);
      if (result != map || !"video/mp4".equals(get.invoke(result, "mimeType"))) {
        throw new AssertionError("Sharing must receive the original ReadableMap");
      }
      if (title != null && !title.equals(get.invoke(result, "dialogTitle"))) {
        throw new AssertionError("Share title changed in native conversion");
      }
    }
    System.out.println("PASS: release shareAsync options conversion, all destinations, Hindi and optional title");
    Method typeOf = Class.forName(names[12]).getMethod(names[13], Class.class);
    String prefix = "expo.modules.filesystem.legacy.";
    Object[][] cases = {
      {"DeletingOptions", "idempotent", true},
      {"MakeDirectoryOptions", "intermediates", true},
      {"InfoOptionsLegacy", "md5", true},
      {"RelocatingOptions", "from", "file:///cache/reel.mp4", "to", "file:///files/shared-reels/reel.mp4"},
      {"DownloadOptionsLegacy", "md5", true, "cache", false}
    };
    Method putBoolean = mapClass.getMethod("putBoolean", String.class, boolean.class);
    for (Object[] test : cases) {
      Class<?> recordClass = Class.forName(prefix + test[0]);
      Object recordConverter = obtain.invoke(provider, typeOf.invoke(null, recordClass));
      Object input = mapClass.getConstructor().newInstance();
      for (int i = 1; i < test.length; i += 2) {
        if (test[i + 1] instanceof Boolean) putBoolean.invoke(input, test[i], test[i + 1]);
        else put.invoke(input, test[i], test[i + 1]);
      }
      if (test[0].equals("DownloadOptionsLegacy")) {
        Object headers = mapClass.getConstructor().newInstance();
        put.invoke(headers, "Authorization", "Bearer test-token");
        mapClass.getMethod("putMap", String.class, Class.forName("com.facebook.react.bridge.ReadableMap"))
            .invoke(input, "headers", headers);
      }
      Object result = convert.invoke(recordConverter, input, null, false);
      for (int i = 1; i < test.length; i += 2) {
        Field field = recordClass.getDeclaredField((String) test[i]);
        field.setAccessible(true);
        if (!test[i + 1].equals(field.get(result))) {
          throw new AssertionError(test[0] + "." + test[i] + " was not converted correctly");
        }
      }
      if (test[0].equals("DownloadOptionsLegacy")) {
        Field headersField = recordClass.getDeclaredField("headers");
        headersField.setAccessible(true);
        if (!"Bearer test-token".equals(((Map<?, ?>) headersField.get(result)).get("Authorization"))) {
          throw new AssertionError("Download authorization headers were lost");
        }
      }
      System.out.println("PASS: release file preparation " + test[0]);
    }
  }
}
