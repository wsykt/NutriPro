package com.health;

import java.io.*;
import java.util.jar.*;
import java.util.zip.*;
import java.util.*;

public class Repackager {
    public static void main(String[] args) throws Exception {
        String sourceDir = args[0];  // target/_extract
        String outputJar = args[1];  // target/health-backend-1.0.0.jar

        System.out.println("Source dir: " + sourceDir);
        System.out.println("Output jar: " + outputJar);

        File dir = new File(sourceDir);
        if (!dir.isDirectory()) {
            System.err.println("ERROR: source is not a directory");
            System.exit(1);
        }

        // Read MANIFEST.MF
        Manifest manifest = new Manifest();
        File mfFile = new File(dir, "META-INF/MANIFEST.MF");
        if (mfFile.exists()) {
            FileInputStream fis = new FileInputStream(mfFile);
            manifest.read(fis);
            fis.close();
            System.out.println("Manifest loaded: " + mfFile.getAbsolutePath());
        } else {
            System.out.println("WARNING: No MANIFEST.MF found, creating default");
        }

        // Create output jar
        FileOutputStream fos = new FileOutputStream(outputJar);
        JarOutputStream jos = new JarOutputStream(fos, manifest);

        // Walk directory and add entries
        List<File> allFiles = new ArrayList<>();
        collectFiles(dir, allFiles);
        System.out.println("Found " + allFiles.size() + " entries");

        int count = 0;
        int nestedJars = 0;
        for (File f : allFiles) {
            String relative = f.getAbsolutePath().substring(dir.getAbsolutePath().length() + 1);
            relative = relative.replace(File.separatorChar, '/');
            if (relative.equals("META-INF/MANIFEST.MF")) continue;

            // Spring Boot rules:
            // - Nested jars (BOOT-INF/lib/*.jar, BOOT-INF/classes/*.jar): STORE (no compression)
            // - Class files and resources in BOOT-INF/classes: DEFLATE (compressed)
            // - Top-level launcher classes: DEFLATE (compressed)
            boolean isNestedJar = relative.startsWith("BOOT-INF/lib/") && relative.endsWith(".jar");
            int method = isNestedJar ? JarEntry.STORED : JarEntry.DEFLATED;

            byte[] content = readFile(f);
            JarEntry entry;
            if (method == JarEntry.STORED) {
                entry = new JarEntry(relative);
                entry.setSize(content.length);
                entry.setCompressedSize(content.length);
                CRC32 crc = new CRC32();
                crc.update(content);
                entry.setCrc(crc.getValue());
                entry.setMethod(ZipEntry.STORED);
                nestedJars++;
            } else {
                entry = new JarEntry(relative);
                entry.setMethod(ZipEntry.DEFLATED);
            }
            entry.setTime(f.lastModified());

            jos.putNextEntry(entry);
            jos.write(content);
            jos.closeEntry();
            count++;
        }

        jos.close();
        fos.close();
        System.out.println("Done! " + count + " entries written (" + nestedJars + " nested jars STORED)");
        System.out.println("Output: " + new File(outputJar).length() + " bytes");
    }

    private static void collectFiles(File dir, List<File> result) {
        File[] files = dir.listFiles();
        if (files == null) return;
        for (File f : files) {
            if (f.isDirectory()) {
                collectFiles(f, result);
            } else {
                result.add(f);
            }
        }
    }

    private static byte[] readFile(File f) throws Exception {
        byte[] buf = new byte[(int) f.length()];
        FileInputStream fis = new FileInputStream(f);
        int read = 0;
        int total = 0;
        while (total < buf.length && (read = fis.read(buf, total, buf.length - total)) > 0) {
            total += read;
        }
        fis.close();
        return buf;
    }
}
